# Plan of the day

1. 🏗️ **Data product setup**: walk through the full setup from scratch with a dummy/placeholder transformer
2. ☁️ **First cloud deploy**: verify the dummy data product builds and deploys successfully in the cloud
3. 📊 **Create a BigQuery input table**: write a minimal dbt model to land data in BQ
4. 🔑 **Permissions**: configure a service account and grant the required BigQuery permissions
5. 🔌 **Connect & validate**: test the BigQuery connection locally, then deploy and validate in the cloud
6. 📤 **ClickHouse output port**: write results to the analytic output port using the ClickHouse client
7. 🚀 **Full pipeline deploy**: deploy the complete pipeline and verify end-to-end in the cloud
8. 🔄 **Meaningful data**: circle back to step 3 and replace the placeholder with a real BigQuery model

---

# Setting up a new Data Product

## 1. Create the data product

- Go to [data-product-management.tst.uitwisselingsplatform.be](https://data-product-management.tst.uitwisselingsplatform.be) (password in Bitwarden)
- Go to **Mijn data producten** > **Dataproduct aanmaken**
- Fill in the form (domain: `wp1`)
- Open your data product, click the Bitbucket repo link, and copy the SSH clone URL

## 2. Set up Git / SSH

Follow the Bitbucket SSH key guide for your OS:

- [macOS](https://support.atlassian.com/bitbucket-cloud/docs/set-up-personal-ssh-keys-on-macos/)
- [Windows](https://support.atlassian.com/bitbucket-cloud/docs/set-up-personal-ssh-keys-on-windows/)
- [Linux](https://support.atlassian.com/bitbucket-cloud/docs/set-up-personal-ssh-keys-on-linux/)

> **Important:** Bitbucket is stricter than GitHub — you must explicitly tell SSH which key to use. Add the following to `~/.ssh/config`:
>
> ```
> Host bitbucket.org
>   HostName bitbucket.org
>   User git
>   IdentityFile ~/.ssh/{name-of-your-bitbucket-private-key}
>   IdentitiesOnly yes
> ```

After this one-time setup, clone your Bitbucket repo using the SSH URL from step 1.

## 3. Copy the boilerplate

Clone the boilerplate **outside** the repo you just cloned (putting it inside would create a Git conflict):

```
https://github.com/cultuurnet/uwp-dp-boilerplate
```

Copy all files from the boilerplate into your Bitbucket repo folder. Make sure **not to copy the`.git` folder** from the boilerplate code.

The boilerplate provides the dev container setup and abstracts away the connections with ClickHouse and BigQuery, so you don't have to rewrite that logic or fiddle with settings for every new data product.

## 4. Set up the dev container in VS Code

Install the official [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension by Microsoft.

To open your project inside the container:

- Open the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`)
- Run: **Dev Containers: Rebuild and Reopen in Container**

> **Note:** Some VS Code extensions (e.g. Claude) need to be reinstalled inside the dev container — they don't carry over automatically from your host environment.

## 5. Deploy a dummy data product

Fill in the `dataproduct.yaml` file first and get everything working without any input or output ports connected. Then push to remote `main`.

Pushing to `main` triggers an automatic build. To follow progress:

1. Go to [data-product-management.tst.uitwisselingsplatform.be](https://data-product-management.tst.uitwisselingsplatform.be)
2. **Mijn dataproducten** > your data product > **Logs**
3. You should see: `build started` → `build completed`

To deploy after a successful build:

4. Switch from the **Logs** tab to the **Deploy product** tab
5. Click **Deploy dataproduct**
6. Two new log entries appear: `deploy started` → `deploy completed`

> **Tip on debugging:** Logs are sometimes incomplete or cut off. Take small steps, push frequently, and verify each piece works before moving on — the build/deploy cycle is slow so balance the push sizes.

This completes the first milestone: a dummy data product running in the cloud.

---

# BigQuery input port

## 1. Create a dbt model

Create a dbt model in `/workspaces/data-container/src/dbt/sql_pipelines/models/uwp/`. Start with something like:

```sql
/*
Collect UiTPAS passholder ticketsales for use in UWP dataproduct.
Data processed by this query is quite small (less then 1.5GB), therefore 'table' materialization is chosen
instead of 'incremental' to simplify the script.
*/

{{
    config(
        materialized='table',
    )
}}

SELECT x, y, z FROM ref/source('some_source')
```

Compile first to verify the generated SQL, then run:

```bash
conda activate dbt-container-env && dbt compile --target dev --select "name-of-your-model" --vars '{"date":"2026-05-08"}'
```

```bash
conda activate dbt-container-env && dbt run --target dev --select "name-of-your-model" --vars '{"date":"2026-05-08"}'
```

> **Warning:** If you have not used `dbt run` before, ask a colleague first — an incorrect run can overwrite production tables.

## 2. Set up a service account

UWP is external to our GCP setup, so you need a service account to access BigQuery.

---

**Isolate your data for your dataproduct in one dataset in BigQuery**

- UWP service accounts (SA) will be scoped to ONE dataset in the reporting project.
- Accounts will get privileges for specific tables within that dataset.
- SA are created for dev/test/prod environments. Make sure datasets exist in all environments, otherways SA creation will fail.

**Configure SA in Terraform**

- You can add a new service account by creating a PR in the [infra-repo](https://github.com/cultuurnet/data-GCP-infrastructure/tree/main/infra/applications/uwp)
- Or you can ask Elia or Bo, they have experience

**Generate a key file:**
After these service accounts are created, you can get your keys via a command like so
```bash
gcloud iam service-accounts keys create survey-key-prod.json --iam-account uwp-survey-prod@reporting-224812.iam.gserviceaccount.com
```
Where you need to replace the email address with the email address of the SA you are interested in.
This generates a `.json`file which are your "credentials". 
It is those credentials, or "keys" that the dataproduct needs to have in order to function properly.

---

## 3. Configure credentials in your dataproduct

Copy the file contents into `secrets.yaml`. If your `dataproduct.yaml` has:

```yaml
secretEnvironmentVariables:
  jsonCredentials: "jsonCredentials"
```

Then `secrets.yaml` should look like (note the pipe and indentation):

```yaml
jsonCredentials: |
  {
    "type": "service_account",
    "project_id": "reporting-224812",
    "private_key_id": "b74c49******9d438f",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMI******PC8=\n-----END PRIVATE KEY-----\n",
    "client_email": "******@reporting-224812.iam.gserviceaccount.com",
    "client_id": "114867*****67",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/uwp-uitpas-dev%40reporting-224812.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
  }
```

## 4. Test locally

In `main.py`:

```python
bqc = BigQueryClient()
query = """
    SELECT
        some_col
    FROM
        some_table
    LIMIT 10
"""
df = bqc.execute_query(query)  # returns a Polars DataFrame
print(df)
```

**Useful debugging snippets:**

Verify if a env var is set
```python
json_credentials = get_environment_variable("INPUT.googlebigquery.jsonCredentials", None)
if not json_credentials:
    raise ValueError("INPUT.googlebigquery.jsonCredentials is not set")
```

Debugging memory issues
```python
memory_bytes = df.estimated_size()
print(f"DataFrame size in memory: {memory_bytes / 1024 / 1024:.2f} MB ({df.shape[0]} rows x {df.shape[1]} cols)")
```

For debugging env vars, remove this when deploying to cloud as it will print secrets to logs.
```python
import os
print(os.environ)
```

### Memory usage comparison (Polars vs Pandas vs list of dicts)

For reference, here are the in-memory sizes for the UiTPAS ticket sales dataset (1,077,026 rows × 11 cols):

| Format | Memory usage |
|---|---|
| Polars DataFrame | 106.51 MB |
| Pandas DataFrame | 389.87 MB |
| List of dicts | 485.65 MB |

Polars is significantly more memory-efficient. Keep this in mind when sizing your transformer — for large tables you'll need to set `memory: HUGE` in `dataproduct.yaml` (gives the VM 3 GB):

```yaml
spec:
  transformer:
    memory: "HUGE"
```

**Code to reproduce the comparison:**

```python
# Polars
memory_bytes = df.estimated_size()
print(f"DataFrame size in memory: {memory_bytes / 1024 / 1024:.2f} MB ({df.shape[0]} rows x {df.shape[1]} cols)")

# Pandas
pdf = df.to_pandas()
pandas_bytes = pdf.memory_usage(deep=True).sum()
print(f"Pandas DataFrame size in memory: {pandas_bytes / 1024 / 1024:.2f} MB ({pdf.shape[0]} rows x {pdf.shape[1]} cols)")

# List of dicts
import sys
records = df.to_dicts()
list_bytes = sys.getsizeof(records) + sum(sys.getsizeof(r) for r in records)
print(f"List of dicts size in memory: {list_bytes / 1024 / 1024:.2f} MB ({len(records)} records)")
```

Run `dp run -v` to verify the BigQuery connector is working locally.

## 5. Deploy with credentials

Push to remote `main`. Once the build completes successfully, go to the **Deploy** tab and paste the JSON contents from `secrets.yaml` into the credentials field before deploying.

## 6. Connect the ClickHouse output port

In `main.py`, add the ClickHouse client. Expand your query, then start with a truncate + insert of the Polars DataFrame. Once that works, you can query the output port for the latest record date and switch to an incremental insert instead of a full truncate.

---

# TODO

- Add option B: use a different input port type??

---

# Links

| Resource | URL |
|---|---|
| Full docs (public) | [uitwisselingsplatform.atlassian.net](https://uitwisselingsplatform.atlassian.net/wiki/spaces/DDTC) |
| UWP dev environment | [data-product-management.tst.uitwisselingsplatform.be](https://data-product-management.tst.uitwisselingsplatform.be/) (pw in Bitwarden) |
| UWP production | [data-product-management.uitwisselingsplatform.be](https://data-product-management.uitwisselingsplatform.be/) (pw via itsme) |
| Boilerplate repo (public) | [github.com/cultuurnet/uwp-dp-boilerplate](https://github.com/cultuurnet/uwp-dp-boilerplate) |