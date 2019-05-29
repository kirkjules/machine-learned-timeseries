# htp: A High Throughput Python Package to Query FX, Develop Trading Strategies and Establish a Live Platform.

### Introduction

* No package exists that incorporates all aspects of financial timeseries quantative technical analysis, including the data exploration, strategy design and testing, and live deployment.
* The aim is to provide a complete pipeline that can be used in parts or entirely.
  * The project will utilise minimum dependencies. Those that are required will individually possess thorough documentation. This facilitates efficient troubleshooting and educates on best practises.
* Once completed, this project will overcome issues that prevent success in financial analysis with python.
  * Notably, the initial up-skilling required to leverage the power and efficiency that python provides.

### Technologies

* The focus dataset will be FX and CFD, as afforded by Oanda's v20 API.
  * However, the implicit modular structure of the project will accommodate externally sourced timeseries data for evaluation and visualisation.
* Key dependencies are Pandas, for data housing, and Flask, for project structure. Additionally, AWS Lambda will be used for multiprocessing requirements.
* This is an endeavour to produce a polished body of work written in python 3.7. The test of this project will be its ability to evolve with new technologies as they become available.

### Information Funnel

Stage 1     | Stage 2                     | Stage 3
------------|-----------------------------|----------
Acquisition | Cleanse, store and evaluate | Visualise

###### Stage 1 - Acquisition

* Achieved by interfacing with a readily available API that can query a broad library of tickers.
  * Initially the `api` module will be written to interface with Oanda's V20 API.
  * As the module develops it will house functionality to engage with other ticker APIs such as AlphaAdvantage.
* Functionality built for acquisition is designed as generally as possible. This encourages the user to take responsibility for the inputs that will define the shape and behaviour of the returning data.
* The `toolbox` module contains features that facilitate input generation and function optimisation across the whole package. Again, these features will remain general to tasks that are common to financial technical analysis.
  * As a result, users can opt to define their own functions, inline with preset specifications, to make them compatible with availble optimisation features.
