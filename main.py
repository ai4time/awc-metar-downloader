import math
import os
import time
from datetime import datetime

import anylearn
import click

from ingestion import (
    fetch_stations,
    AviationWeatherCenterMetarDownloader,
    WeatherGovMetarDownloader,
)
from ingestion.logger import logger


if os.environ.get('ANYLEARN_TASK_ID', None) is not None:
    data_workspace = anylearn.get_dataset("yhuang/METARs").download()
else:
    data_workspace = "./data"


@click.group()
@click.version_option()
def main():
    pass


@main.command()
@click.option(
    '--hours',
    type=click.IntRange(0, 120),
    default=1,
    help="Back hours to search on Aviation Weather Center.",
)
@click.option(
    '--interval',
    default=600,
    help="Polling interval in seconds.",
)
def poll(hours, interval):
    stations = fetch_stations() # 9318 stations
    downloader = AviationWeatherCenterMetarDownloader(
        stations=stations,
        target_dir=data_workspace,
    )
    # URL length limit ~8000
    # while each station = 4 digits code + 1 comma encoded in %2C
    CHUNK_SIZE = 1050
    while True:
        for i in range(0, len(stations.keys()), CHUNK_SIZE):
            candidates = list(stations.values())[i:i+CHUNK_SIZE]
            while not downloader.download1(
                stations_to_search=candidates,
                hours=hours,
            ):
                time.sleep(10)
        time.sleep(interval)


@main.command()
@click.option(
    '--from-datetime',
    default=datetime.now().strftime("%Y%m%d%H%M"),
    help="From datetime in format %Y%m%d%H%M.",
)
@click.option(
    '--hours',
    type=click.IntRange(0, 120),
    default=120,
    help="Back hours to search on Aviation Weather Center.",
)
def fill(from_datetime, hours):
    stations = fetch_stations() # 9318 stations
    downloader = AviationWeatherCenterMetarDownloader(
        stations=stations,
        target_dir=data_workspace,
    )
    # Too much content will cause AWC to return 500
    CHUNK_SIZE = 100
    N = math.ceil(len(stations.keys()) / CHUNK_SIZE)
    for i in range(0, len(stations.keys()), CHUNK_SIZE):
        candidates = list(stations.values())[i:i+CHUNK_SIZE]
        while not downloader.download1(
            stations_to_search=candidates,
            from_datetime=datetime.strptime(from_datetime, "%Y%m%d%H%M"),
            hours=hours,
        ):
            time.sleep(10)
        logger.info(f"Downloaded {int(1+i/CHUNK_SIZE)}/{N}")
        time.sleep(10)


@main.command()
@click.option(
    '--start',
    help="Start datetime in format %Y%m%d%H%M.",
)
@click.option(
    '--end',
    help="End datetime in format %Y%m%d%H%M.",
)
def batch(start, end):
    stations = fetch_stations() # 9318 stations
    downloader = WeatherGovMetarDownloader(
        stations=stations,
        target_dir=data_workspace,
    )
    # URL length limit ~8000
    # while each station = 4 digits code + 1 comma encoded in %2C
    CHUNK_SIZE = 1050
    N = math.ceil(len(stations.keys()) / CHUNK_SIZE)
    for i in range(0, len(stations.keys()), CHUNK_SIZE):
        candidates = list(stations.values())[i:i+CHUNK_SIZE]
        while not downloader.download1(
            stations_to_search=candidates,
            start_datetime=datetime.strptime(start, "%Y%m%d%H%M"),
            end_datetime=datetime.strptime(end, "%Y%m%d%H%M"),
        ):
            time.sleep(10)
        logger.info(f"Downloaded {int(1+i/CHUNK_SIZE)}/{N}")
        time.sleep(10)


if __name__ == "__main__":
    main()
