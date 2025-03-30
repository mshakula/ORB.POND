#!/usr/bin/env python3

import concurrent.futures
import threading
import time
import pytest


def run_function(pool, i):
    print(f"{pool} Function {i} in process {threading.get_native_id()}")
    time.sleep(i)


def submit_to_pool(pool, i):
    fut = pool.submit(run_function, type(pool), i)
    fut.add_done_callback(
        lambda fut: print(
            f"{type(pool)} Future {i} callback {
                threading.get_native_id()}: {fut.result()}"))
    return fut


def test_pool_ids_threads():
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=5)
    futures = [submit_to_pool(pool, i) for i in range(1, 5)]


def test_pool_ids_subprocess():
    pool = concurrent.futures.ProcessPoolExecutor(max_workers=5)
    futures = [submit_to_pool(pool, i) for i in range(1, 5)]


if __name__ == "__main__":
    test_pool_ids_threads()
    test_pool_ids_subprocess()
