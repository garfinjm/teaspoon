FROM mambaorg/micromamba:1.4.9 as app

ARG SOFTWARENAME_VERSION="0.3.0"

USER root

WORKDIR /

LABEL base.image="mambaorg/micromamba:1.4.9"
LABEL dockerfile.version="2"
LABEL software="teaspoon"
LABEL software.version="${SOFTWARENAME_VERSION}"
LABEL description="Quickly downsample Illumina PE reads to an approximate coverage, without a known genome size."
LABEL website="https://github.com/garfinjm/teaspoon"
LABEL license="https://github.com/garfinjm/teaspoon/blob/master/LICENSE"
LABEL maintainer="Jake Garfin"
LABEL maintainer.email="garfinjm@gmail.com"

RUN apt-get update && apt-get install -y --no-install-recommends \
 wget \
 ca-certificates \
 procps && \
 apt-get autoclean && rm -rf /var/lib/apt/lists/*

 RUN wget https://github.com/garfinjm/teaspoon/archive/refs/tags/${SOFTWARENAME_VERSION}.tar.gz && \
  tar -xvf ${SOFTWARENAME_VERSION}.tar.gz && \
  rm ${SOFTWARENAME_VERSION}.tar.gz

RUN micromamba install --name base -c conda-forge -c bioconda -c defaults -f ./teaspoon-${SOFTWARENAME_VERSION}/environment.yml && \
 micromamba clean -a -y && \
 mkdir /data

ENV PATH="/teaspoon-${SOFTWARENAME_VERSION}:/opt/conda/bin/:${PATH}" \
 LC_ALL=C.UTF-8

#CMD [ "teaspoon.py", "--help" ]

WORKDIR /data

##### ----- ----- ----- ----- ----- ----- ----- ----- ----- ----- ----- #####
##### Step 2. Set up the testing stage.                                 #####
##### The docker image is built to the 'test' stage before merging, but #####
##### the test stage (or any stage after 'app') will be lost.           #####
##### ----- ----- ----- ----- ----- ----- ----- ----- ----- ----- ----- #####

# A second FROM insruction creates a new stage
# new base for testing
#FROM app as test

# so that conda/micromamba env is active when running below commands
#ENV ENV_NAME="base"
#ARG MAMBA_DOCKERFILE_ACTIVATE=1

# set working directory so that all test inputs & outputs are kept in /test
#WORKDIR /test

# print help and version info; check dependencies (not all software has these options available)
# Mostly this ensures the tool of choice is in path and is executable
#RUN teaspoon.py --help
# softwarename --check && \
# softwarename --version

# Run the program's internal tests if available, for example with SPAdes:
#RUN spades.py --test

# Option 1: write your own tests in a bash script in the same directory as your Dockerfile and copy them:
#COPY my_tests.sh .
#RUN bash my_tests.sh

# Option 2: write below common usage cases
# Add back tests at a later date
#RUN wget ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR166/009/ERR1664619/ERR1664619_1.fastq.gz && \
#    wget ftp://ftp.sra.ebi.ac.uk/vol1/fastq/ERR166/009/ERR1664619/ERR1664619_2.fastq.gz && \
#    teaspoon.py -c 10 -r1 ERR1664619_1.fastq.gz -r2 ERR1664619_2.fastq.gz && \
#    tablespoon.py -c 10 -i . -o ./tablespoon_output