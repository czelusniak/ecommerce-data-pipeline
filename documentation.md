# Documentação Técnica do Projeto Ecommerce Data Pipeline

## 1. Visão Geral (O "O quê")
Este projeto implementa um pipeline de engenharia de dados (Data Engineering) concebido para simular a extração, carregamento e transformação (ELT) de dados de um sistema de E-commerce. O objetivo principal do projeto é automatizar o fluxo de dados desde a origem (uma API fake e arquivos CSV) até um Data Warehouse, garantindo que os dados sejam limpos, padronizados e agregados de forma a ficarem prontos para análise de negócios. 
O pipeline orquestra tanto a ingestão de dados crus via requisições HTTP para a FakeStore API, gravando-os diretamente em um banco de dados Snowflake, quanto a transformação de dados locais via seeds no dbt.

## 2. Stack Tecnológica
* **Linguagem de Programação:** Python (versão >= 3.10)
* **Orquestração de Workflows:** Apache Airflow (versão 2.10.x), configurado com CeleryExecutor, PostgreSQL (backend) e Redis (broker).
* **Data Warehouse / Computação em Nuvem:** Snowflake
* **Transformação de Dados:** dbt (Data Build Tool) com o plugin `dbt-snowflake`
* **Containerização:** Docker e Docker Compose (Airflow Services + Container Dedicado para rodar comandos CLI do dbt e injetar os profiles)
* **Extração de Dados:** Biblioteca `requests` do Python e `pandas` para manipulação em memória.

## 3. Fluxo de Execução (O "Como")
A orquestração do pipeline é dividida em duas grandes DAGs (Directed Acyclic Graphs) executadas pelo Airflow:

### Fase 1: Ingestão de Dados (`01_ingest_ecommerce`)
1. **Extração:** A DAG do Airflow dispara requisições HTTP GET à *FakeStore API* buscando dados dos sub-domínios `/products` e `/carts`.
2. **Transformação Mínima em Memória (Pandas):** Os dados recebidos em formato JSON são transformados em um DataFrame do Pandas. Colunas com estruturas complexas (como listas ou dicionários em carrinhos de compras) são achatadas para strings `df[col] = df[col].astype(str)` para compatibilidade com SQL. É também adicionada uma coluna de metadado (`extracted_at`) com a data e hora da extração.
3. **Carga Segura (Load):** O Airflow utiliza um hook (`SnowflakeHook(snowflake_conn_id='snowflake_default')`) para conectar-se ao Snowflake. Usando o SQLAlchemy, o DataFrame é enviado de uma vez (`chunksize=1000`) utilizando o método `to_sql` para a camada Bronze/Raw (`ECOMMERCE_DB.RAW_DATA`) as tabelas `products` e `carts`.

### Fase 2: Transformação Pós-Carga (`dbt-snowflake-process`)
Esta DAG é desenhada para usar O operador Docker do Airflow para subir um container efêmero construído a partir de [src/Dockerfile](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/src/Dockerfile), que possui as ferramentas do dbt configuradas. A DAG executa três tarefas sequenciais.
1. **`run_seeds`:** O container roda o comando `dbt seed`, importando os dados CSV locais (como [customers.csv](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/src/dbt/seeds/customers.csv), [bookings_1.csv](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/src/dbt/seeds/bookings_1.csv), etc.) presentes na pasta `src/dbt/seeds/` para o Snowflake.
2. **`run_staging`:** O container roda `dbt run --select 1staging`. Isto aplica modelos SQL focados em limpeza básica, conversões de timestmaps e renomeação de colunas sobre os dados brutos recém incluídos.
3. **`run_intermediate_and_marts`:** Por fim, roda `dbt run --select 2intermediate 3marts`. Os scripts na camada intermediária pegam os dados da camada staging, aplicam as lógicas de negócios (fazendo *joins* entre carrinhos, produtos e itens de pedidos), até aterrissarem em *marts*, prontas para consumo por BI/Analytics.

## 4. Principais Componentes
* **`/airflow/dags/`**: Contém o coração da lógica de orquestração.
  * [ingest_ecommerce.py](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/airflow/dags/ingest_ecommerce.py): Responsável por baixar os dados da web, aplicar limpeza inicial limitadíssima e fazer a gravação nativa no Snowflake através do conector Airflow/SQLAlchemy.
  * [docker-dbt-snowflake.py](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/airflow/dags/docker-dbt-snowflake.py): Lida com o acionamento via DockerOperator da máquina que faz o building do modelo dbt.
* **[/airflow/docker-compose.yaml](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/airflow/docker-compose.yaml)**: Infraestrutura que dá vida ao Airflow local do projeto de forma isolada, contendo os serviços Webserver, Scheduler, Celery Worker, Triggerer, Redis e o Postgres. Além de expor dinamicamente a porta proxy do Docker nativo local (isso permite os containers Airflow criarem subcontainers para rodar o dbt).
* **`/src/dbt/`**: A sub-árvore do projeto dbt.
  * `seeds/`: Arquivos CSV mockados contendo transações legadas, de bookings, desenvolvedores ou base de clientes iniciais.
  * `models/staging/`: Códigos SQL (*models*) que materializam views/tabelas da camada Staging, consumindo `source`s do Data Warehouse.
  * `models/intermediate/`: Modelos com junção de lógicas de negócio crucias ([int_order_items.sql](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/src/dbt/models/intermediate/int_order_items.sql) e definitions de schemas).
* **[/src/Dockerfile](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/src/Dockerfile)**: Receita enxuta baseada em `python:3.12-slim` que apenas copia os arquivos do dbt para a imagem e instala os pacotes python necessários (`dbt`, `dbt-snowflake`).
* **`scripts/snowflake-setup.sql`**: Um roteiro único de DDL (Data Definition Language) de configuração da infraestrutura no Warehouse, preparando Warehouse, Schemas, Roles e privilégios.

## 5. Pontos de Atenção (Opcional)
* **`Docker-in-Docker Proxy` na DAG do DBT:** A DAG de processamento ([docker-dbt-snowflake.py](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/airflow/dags/docker-dbt-snowflake.py)) depende da criação de novos containers Docker por meio do próprio DockerOperator (`docker_url="tcp://docker-proxy:2375"`). Para que o container Worker do Airflow fizesse isso com sucesso, foi criado um serviço adicional `docker-proxy` dentro do [docker-compose.yaml](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/airflow/docker-compose.yaml) construíndo um túnel com as APIs unix do daemon do Docker base local.
* **Achatamento (Flatten) agressivo para Strings:** Durante a etapa de ingestão do pandas, qualquer coluna que o pandas reconheça como sendo lista ou dicionário é convertida agressivamente para `string`. Embora o Snowflake tenha suporte soberbo para analisar JSON de forma nativa (`VARIANT`), esta abordagem é tomada provavelmente por limitações simplórias do comando `.to_sql()`. Se houver atualizações futuras para lidar com as nested lists do JSON, deve ser priorizada a estratégia de salvar diretamente o objeto JSON num formato de dados semi-estruturado `VARIANT` nas tabelas Snowflake para permitir processamento otimizado futuramente pelo comando de *FLATTEN* próprio do DB em vez de processamento in-memory com Python.
* **Drop Table Padrão (Full Refresh):** A rotina de ingestão do Python roda com `if_exists='replace'`, ou seja, apaga todo o histórico da tabela `RAW_DATA.products` e `carts` diariamente (`@daily`) substituindo-o pela carga mais recente em vez de processar via `UPSERT`/`MERGE`. Isto torna a rastreabilidade do histórico impossível (já que os dados cruzeram reescritos), recomendável rever caso esse projeto escale a níveis de Big Data.
* **Inconsistência de Pastas `marts` X README:** O [README.md](file://wsl.localhost/Ubuntu/home/ygritte/docker/ecommerce-data-pipeline/README.md) informa a existência do modelo em modelo em três diretórios: `1staging`, `2intermediate` e `3marts`. No momento, apenas as subpastas `staging` e `intermediate` existem dentro de `src/dbt/models/`. Pode ser um trabalho não concluído ou algo pendente de refatoração para separar corretamente a view de "Gold" / Presentation.
