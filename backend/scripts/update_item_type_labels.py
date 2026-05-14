from pathlib import Path
import sys

from google.cloud import bigquery

sys.path.append(str(Path(__file__).resolve().parents[1]))

from utils.config import BIGQUERY_DATASET, GCP_PROJECT_ID


ITEM_TYPE_RENAMES = {
    "Chemical": "Hazardous Chemical",
    "Finished Goods": "Finished Product",
    "Raw Material": "Production Material",
    "Packaging": "Packaging Supply",
    "Maintenance Part": "Maintenance Spare Part",
}


def quoted(value: str) -> str:
    return "'" + value.replace("'", "\\'") + "'"


def main():
    client = bigquery.Client(project=GCP_PROJECT_ID)
    dataset_id = f"{GCP_PROJECT_ID}.{BIGQUERY_DATASET}"
    inventory_table = f"`{dataset_id}.inventory_map`"
    rack_table = f"`{dataset_id}.rack_master`"

    for old_label, new_label in ITEM_TYPE_RENAMES.items():
        client.query(
            f"""
            UPDATE {inventory_table}
            SET item_type = {quoted(new_label)}
            WHERE item_type = {quoted(old_label)}
            """
        ).result()

    cases = " ".join(
        f"WHEN item_type = {quoted(old_label)} THEN {quoted(new_label)}"
        for old_label, new_label in ITEM_TYPE_RENAMES.items()
    )

    client.query(
        f"""
        UPDATE {rack_table}
        SET allowed_item_types = ARRAY(
            SELECT CASE {cases} ELSE item_type END
            FROM UNNEST(allowed_item_types) AS item_type
        )
        WHERE TRUE
        """
    ).result()

    print("Updated inventory_map.item_type and rack_master.allowed_item_types labels")


if __name__ == "__main__":
    main()
