# zkml

The ZKML is TODO

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

Ensure that the packages are hashed and configured:
- `autonomy analyse service --public-id valory/zkml:0.1.0`
- `autonomy hash all`
- `autonomy packages lock`
- `autonomy push-all --remote`

Then run the following commands:
1. `autonomy fetch valory/zkml:0.1.0 --service --local`
2. `cd zkml/`
3. `autonomy build-image`
4. Create the agent's key:
    ```bash
    autonomy generate-key -n 1 ethereum
    ```

5. `autonomy deploy build keys.json -ltm`
6. `autonomy deploy run --build-dir abci_build/`
7. In a separate terminal: `docker logs abci0 -f`
8. Test the service endpoints (in another terminal):
     ```bash
     TODO
     ```
