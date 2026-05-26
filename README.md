# cbio-ingest-cli

This software is a CLI that communicates with the
[cbio-ingest](https://github.com/bihealth/cbio-ingest) REST API server.

## Installation

Make sure to have
[uv](https://docs.astral.sh/uv/getting-started/installation/) installed.

Then, do:

```bash
git clone https://github.com/bihealth/cbio-ingest-cli.git
cd cbio-ingest-cli
uv sync
source .venv/bin/activate
```

## Configuration

Create a configuration:

```bash
mkdir -p ~/.config/cbio-ingest
cat <<EOF > ~/.config/cbio-ingest/config.toml
[default]
url = "http://localhost:8000"
token = "mysecrettoken"
EOF
```

## Usage

The main commands are:

```bash
cbio-ingest panel
cbio-ingest study
```

The subcommands for those commands are:

```bash
list    # list all panels or studies available and imported
ingest  # ingest a single panel or study
get     # get more import information for a current panel or study
delete  # delete a panel or study from the database (not from cBioPortal!)
```

### list

The handling for panels and studies is the same.

The `list` command will list all panels that have been placed in the `panel/` folder. All panels that are not imported, are lacking an ID and the status is set to `initial`.

```bash
cbio-ingest panel list

  ID   Name                            Date Created          Status
 ──────────────────────────────────────────────────────────────────────
  1    data_gene_panel_impact300.txt   2026-05-22 10:29:57   completed
  -    data_gene_panel_impact341.txt   -                     initial
  -    data_gene_panel_impact410.txt   -                     initial
  -    data_gene_panel_impact230.txt   -                     initial
  -    data_gene_panel_impact505.txt   -                     initial
  -    data_gene_panel_impact468.txt   -                     initial
```

### ingest

To ingest a panel, provide the filename to the command.
For studies, provide the study folder name.

```bash
cbio-ingest panel ingest data_gene_panel_impact341.txt

Ingestion job submitted for panel 'data_gene_panel_impact341.txt' (id: 2).
```

### get

To retrieve information about the import, provide the id.
To follow the logs, use `--follow`.

```bash
cbio-ingest panel get 2

  ID   Name                            Date Created          Status
 ──────────────────────────────────────────────────────────────────────
  2    data_gene_panel_impact341.txt   2026-05-22 15:26:30   completed

 Timestamp            Level  Reporter  Message
 2026-05-22 15:26:12  INFO   worker    Ingestion started.
 2026-05-22 15:26:12  INFO   worker    Running command: ./importGenePanel.pl --data /panel/data_gene_panel_impact341.txt
 2026-05-22 15:26:19  INFO   docker    Done.
 2026-05-22 15:26:19  INFO   docker    Total time:  7169 ms
 2026-05-22 15:26:30  INFO   worker    Container restarted to apply changes.
 2026-05-22 15:26:30  INFO   worker    Ingestion completed.
```

### delete

Not fully implemented; it will erase only the entry from the import info database, not from cBioPortal.

```bash
cbio-ingest panel delete 2

Panel 2 deleted.
```
