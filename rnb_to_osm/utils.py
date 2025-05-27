from typing import Callable, Generator
from shapely.wkt import loads
from csv import DictReader
import concurrent.futures
from typing import Any


def shape_from_wkt(wkt_shape: str) -> Any:
    if wkt_shape.startswith("SRID="):
        # Extract the actual WKT part after the semicolon
        wkt_shape = wkt_shape.split(";", 1)[1]
    return loads(wkt_shape)


def multithreaded_csv_reader[T](
    file_path: str, f: Callable[[int, dict], T], batch_size=1000, num_threads=8
) -> Generator[T, None, None]:
    def batch_processor(rows):
        return [f(i, row) for (i, row) in rows]

    with open(file_path, mode="r") as file:
        reader = DictReader(file, delimiter=",")
        batch = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []

            i = -1
            for row in reader:
                i += 1
                if i % 100000 == 0:
                    print(f"Yielded {i} entries")
                batch.append((i, row))
                if len(batch) >= batch_size:
                    futures.append(executor.submit(batch_processor, batch))
                    batch = []

            # Submit the last batch if it's not empty
            if batch:
                futures.append(executor.submit(batch_processor, batch))

            # Yield results as they complete
            for future in concurrent.futures.as_completed(futures):
                for result in future.result():
                    yield result
