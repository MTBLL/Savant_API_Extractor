# Savant API Extractor
[![codecov](https://codecov.io/gh/MTBLL/Savant_API_Extractor/graph/badge.svg?token=B63QRXrOeQ)](https://codecov.io/gh/MTBLL/Savant_API_Extractor)
![Mypy](https://github.com/MTBLL/Savant_API_Extractor/actions/workflows/mypy.yml/badge.svg)

## Description
This app pulls in the CSV api endpoint for the Baseball Savant statcast search.
The base url for the search tool is https://baseballsavant.mlb.com/statcast_search/csv? with all the available stats being pulled in for all the players.

This endpoint does not show other leaderboard stats such as Hot Stove Tracker, or rolling windows.
