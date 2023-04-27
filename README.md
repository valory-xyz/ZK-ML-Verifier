# ZK-ML-Verifier

The ZK-ML-Verifier is an Autonolas service which takes up the responsibility of verifying proofs for machine Learning 
models' predictions, using the ZK-ML technique.

You can learn more about it in [this twitter thread](https://twitter.com/autonolas/status/1650869783641083904).

- Clone the repository:

      git clone https://github.com/valory-xyz/ZK-ML-Verifier.git

- System requirements:

    - Python `>= 3.7`
    - [Tendermint](https://docs.tendermint.com/v0.34/introduction/install.html) `==0.34.19`
    - [IPFS node](https://docs.ipfs.io/install/command-line/#official-distributions) `==v0.6.0`
    - [Pipenv](https://pipenv.pypa.io/en/latest/installation/) `>=2021.x.xx`
    - [Docker Engine](https://docs.docker.com/engine/install/)
    - [Docker Compose](https://docs.docker.com/compose/install/)
    - [Node](https://nodejs.org/en) `>=18.6.0`
    - [Yarn](https://yarnpkg.com/getting-started/install) `>=1.22.19`

- Pull pre-built images:

      docker pull valory/autonolas-registries:latest
      docker pull valory/safe-contract-net:latest

- Create development environment:

      make new_env && pipenv shell

- Configure command line:

      autonomy init --reset --author valory --remote --ipfs --ipfs-node "/dns/registry.autonolas.tech/tcp/443/https"

- Pull packages:

      autonomy packages sync --update-packages

## Development

### Testing service locally

This section is under construction as there is no service file implemented yet.
