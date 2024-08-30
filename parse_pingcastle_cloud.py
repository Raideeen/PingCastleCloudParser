"""
* Titre du script: parse_pingcastle_cloud.py

* Description: Ce script permet de parser les résultats de PingCastle Cloud et
  de
les convertir en plusieurs feuilles de calcul Excel pour une analyse plus
rapide. Notamment cela va créer :

- user_roles : décrit les rôles des utilisateurs et si l'utilisateur possède le
  MFA ou non
- apps_summary : résume les applications présente dans le tenant M365, et si
  elle possède des rôles/permissions critiques
- apps_permissions : détaille les permissions des applications présentes dans le
  tenant M365 et si elles sont critiques ou non
- apps_delegate_permissions : détaille les permissions déléguées des
  applications et si elles sont critiques ou non
- apps_roles : détaille les rôles des applications et si ils sont critiques ou
  non

* Auteur: [Adrien Djebar] Contact: [adrien.djebar@proton.me]

* Date de création: [30/04/2024 11:44:32]
* Date de dernière modification: [03/05/2024 18:19:50]

* Instructions:
    1. Assurez-vous que Python est installé sur votre système. De préférence
       Python 3.11
    2. Installez les paquets nécessaires en lançant `pip install -r
       requirements.txt`.
    3. Exécutez le script en tapant `python parse_pingcastle_cloud.py` dans
       votre ligne de commande.

* Notes:
    - Pour plus d'informations sur le fonctionnement du script, veuillez
      consulter
    le README.md.
"""

import argparse
import json
import os
from glob import glob
from pathlib import Path

import pandas as pd

from logger import setup_logger

# Set up logging
logger = setup_logger("parse_pingcastle_cloud")

# APPLICATION EXCEL SHEETS
# Common parameters between each dataframe
general_application_parameters = {
    "appDisplayName": "Display Name",
    "objectId": "Object ID",
    "appId": "App ID",
}

# Define parameters for each dataframe
applications_permissions_params = {
    "record_path": "ApplicationPermissions",
    "prefix": "ApplicationPermissions.",
    "meta": ["appDisplayName", "appId", "objectId"],
    "columns_to_drop": [
        "ApplicationPermissions.permissionId",
        "ApplicationPermissions.principalType",
    ],
    "rename_map": {
        **general_application_parameters,
        "ApplicationPermissions.resourceDisplayName": "resourceDisplayName",
        "ApplicationPermissions.resourceId": "Resource ID",
        "ApplicationPermissions.permission": "Permission Granted",
    },
    "columns_order": [
        "Display Name",
        "Object ID",
        "App ID",
        "resourceDisplayName",
        "Permission Granted",
        "Is Critical ?",
        "Resource ID",
    ],
}

delegated_params = {
    "record_path": "DelegatedPermissions",
    "prefix": "DelegatedPermissions.",
    "meta": ["appDisplayName", "appId", "objectId"],
    "columns_to_drop": ["DelegatedPermissions.principalDisplayName"],
    "rename_map": {
        **general_application_parameters,
        "DelegatedPermissions.consentType": "Consent Type",
        "DelegatedPermissions.resourceId": "Resource ID",
        "DelegatedPermissions.principalId": "Principal ID",
        "DelegatedPermissions.permission": "Scope",
    },
    "columns_order": [
        "Display Name",
        "Object ID",
        "App ID",
        "Consent Type",
        "Scope",
        "Is Critical ?",
        "Principal ID",
        "Resource ID",
    ],
}

application_roles_params = {
    "record_path": "MemberOf",
    "prefix": "MemberOf.",
    "meta": ["appDisplayName", "appId", "objectId"],
    "columns_to_drop": [],
    "rename_map": {
        **general_application_parameters,
        "MemberOf.displayName": "Role Name",
        "MemberOf.roleTemplateId": "Role Template ID",
    },
    "columns_order": [
        "Display Name",
        "Object ID",
        "App ID",
        "Role Name",
        "Role Template ID",
        "Is Critical ?",
    ],
}

# USER ROLES SHEETS
user_roles_params = {
    "record_path": "members",
    "prefix": "Members.",
    "meta": ["Description", "Name"],
    "columns_to_drop": [
        "Members.ObjectId",
        "Members.LastDirSyncTime",
        "Members.IsLicensed",
        "Members.OverallProvisioningStatus",
        "Members.RoleMemberType",
        "Members.ValidationStatus",
        "Members.PasswordNeverExpires",
        "Members.LastPasswordChangeTimestamp",
        "Members.WhenCreated",
        "Members.HasImmutableId",
    ],
    "rename_map": {
        "Name": "Role Name",
        "Description": "Role Description",
        "Members.DisplayName": "User Name",
        "Members.EmailAddress": "Email Address",
        "Members.MFAStatus": "MFA Status",
    },
    "columns_order": [
        "Role Name",
        "User Name",
        "Email Address",
        "MFA Status",
        "Privileged Role ?",
        "Role Description",
    ],
}


def load_data(file_path: str) -> dict:
    """
    Load data from a JSON file.

    Args:
        file_path (str): Path to the JSON file to load

    Returns:
        dict: Data loaded from the JSON file
    """
    try:
        with open(file_path) as f:
            return json.load(f)
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return None
    except Exception as e:
        logger.error(f"An error occured while loading the file: {e}")
        return None

def parse_args():
    """
    Parse arguments for the script.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Parser for PingCastle Cloud JSON files"
    )

    default_file_path = glob("pingcastlecloud_*.json")
    parser.add_argument(
        "--file_path",
        type=str,
        help="Path to the JSON file to parse (relative or absolute). By default, the script will look for any file in the current directory starting with 'pingcastlecloud_' and ending with '.json'.",
        default=default_file_path[0],
    )
    parser.add_argument(
        "--output_path",
        type=str,
        help="Path to the output Excel file (relative or absolute). You must include the file extension (xlsx).",
        default="parsed_pingcastle_cloud_format.xlsx",
    )

    return parser.parse_args()


def handle_non_application_data(df: pd.DataFrame, prefix: str, rename_map: dict):
    """
    Handle the non-application (i.e. user role) data by renaming columns and
    filling the MFA Status column.

    Args:
        - df (pd.DataFrame): DataFrame being processed by the function
          `process_dataframe`
        - prefix (str): A prefix to add when normalizing data from the JSON file
          to avoid having duplicates errors. The prefix change depending on the
          information we want to extract from the JSON file
        - rename_map (dict): Mapping of old column names to new names

    Returns:
        None. Modifies the DataFrame in place.
    """
    # Make the MFA Status column more readable
    new_mfa_status_name = rename_map[f"{prefix}MFAStatus"]

    df[new_mfa_status_name] = (
        df[new_mfa_status_name]
        .astype(str)
        .apply(
            lambda x: "Disabled"
            if x == "['Disabled']"
            else ("Enabled" if x == "['Enabled']" else "To Check Manually")
        )
    )

    # Oddly enough, "Global Administrator" role is named "Company Administrator" in PingCastle Cloud
    role_column = rename_map["Name"]
    df[role_column] = df[role_column].apply(
        lambda x: "Global Administrator" if x == "Company Administrator" else x
    )


def group_data(
    df: pd.DataFrame, group_columns: list, new_index_name: str
) -> pd.DataFrame:
    """
    Creates a new DataFrame with the number of elements in each group with
    additional meta information from the `group_columns` variable.

    Args:
        - df (pd.DataFrame): DataFrame after being processed by the function
          `process_dataframe`
        - group_columns (list): Meta-information to group the data by (e.g.
          ["Display Name", "Object ID", "App ID"])
        - new_index_name (str): Name of the new index column

    Returns:
        pd.DataFrame: A new DataFrame with the number of elements in each group
    """
    return df.groupby(group_columns).size().reset_index(name=new_index_name)


def process_dataframe(
    data: dict,
    record_path: str,
    prefix: str,
    meta: list,
    columns_to_drop: list,
    rename_map: dict,
    columns_order: list,
    isApplicationData: bool,
) -> pd.DataFrame:
    """
    Processes the data from the JSON file depending wether it is application
    data or user roles data.

    Args:
        - data (dict): The source JSON data to process
        - record_path (str): Path in the data where the records are nested
        - prefix (str): A prefix to add when normalizing data from the JSON file
          to avoid having duplicates errors. The prefix change depending on the
          information we want to extract from the JSON file
        - meta (list): List of meta-information to preserve when normalizing the
          data
        - columns_to_drop (list): Columns that should be dropped from the
          dataframe
        - rename_map (dict): Mapping of old column names to new names
        - columns_order (list): Desired order of DataFrame columns. For example,
          ["Display Name", "Object ID", "App ID", "Role Name", "Role Template
          ID", "Is Critical ?"]
        - isApplicationData (bool): Flag to adjust the processing of the data
          depending if we are in the application data or user roles data context

    Returns:
        pandas.DataFrame: A processed DataFrame depending on the context
        (application data or user roles data)
    """
    logger.info(f"Processing data for {record_path}...")
    # Create and process the dataframe
    try:
        df = pd.json_normalize(
            data, record_path=record_path, meta=meta, record_prefix=prefix
        )
    except KeyError as e:
        logger.critical(f"Failed to normalize JSON data: {e}", exc_info=True)
        return pd.DataFrame()  # Return an empty dataframe if an error occurs

    try:
        # Drop columns
        df.drop(columns=columns_to_drop, inplace=True)
    except KeyError as e:
        logger.critical(f"Failed to drop columns: {e}", exc_info=True)

    try:
        # Rename the columns
        df.rename(columns=rename_map, inplace=True)
    except Exception as e:
        logger.warning(f"Failed to rename columns: {e}")

    if isApplicationData:
        # Fill the "None" for the display with AppID_{appID}
        df["Display Name"] = df["Display Name"].fillna(
            "AppID_" + df[rename_map["appId"]]
        )
        # This has to be filled manually in the Excel later
        df["Is Critical ?"] = "To Change"
    else:
        # This has to be filled manually in the Excel later
        df["Privileged Role ?"] = "To Change"
        handle_non_application_data(df, prefix, rename_map)

    # Reorder the columns
    df = df[columns_order]

    return df


def create_summary(
    applications_permissions: pd.DataFrame,
    delegated_permissions: pd.DataFrame,
    applications_roles: pd.DataFrame,
    rename_map: dict,
) -> pd.DataFrame:
    logger.info("Creating summary for all applications...")

    # Define column headers
    HEADER_NUM_APPLICATION_PERMISSIONS = "# Application Permissions"
    HEADER_NUM_APPLICATION_DELEGATED_PERMISSIONS = "# Delegated Permissions"
    HEADER_NUM_APPLICATION_ROLES = "# Roles"

    # Set common index for all frames to streamlines merging
    index_cols = [
        rename_map["appDisplayName"],
        rename_map["objectId"],
        rename_map["appId"],
    ]

    try:
        # Count the number of elements in each dataframe for each elements
        number_of_applications_permissions = group_data(
            application_permissions, index_cols, HEADER_NUM_APPLICATION_PERMISSIONS
        )

        number_of_delegated_permissions = group_data(
            delegated_permissions,
            index_cols,
            HEADER_NUM_APPLICATION_DELEGATED_PERMISSIONS,
        )

        number_of_applications_roles = group_data(
            applications_roles, index_cols, HEADER_NUM_APPLICATION_ROLES
        )

        # Explanation : the asterisk * before index_cols allows to unpack the
        # content of the list
        summary = pd.merge(
            number_of_applications_permissions,
            number_of_delegated_permissions,
            on=[*index_cols],
            how="outer",
        ).merge(number_of_applications_roles, on=[*index_cols], how="outer")

        summary.fillna(0, inplace=True)

        summary[
            [
                HEADER_NUM_APPLICATION_PERMISSIONS,
                HEADER_NUM_APPLICATION_DELEGATED_PERMISSIONS,
                HEADER_NUM_APPLICATION_ROLES,
            ]
        ] = summary[
            [
                HEADER_NUM_APPLICATION_PERMISSIONS,
                HEADER_NUM_APPLICATION_DELEGATED_PERMISSIONS,
                HEADER_NUM_APPLICATION_ROLES,
            ]
        ].astype(int)

        # This has to be filled manually in the Excel later
        summary["Contains Critical Rights ?"] = "To Change"

        return summary
    except Exception as e:
        logger.error(f"An error occured during summary creation: {e}")
        return pd.DataFrame()  # Return an empty dataframe if an error occurs


if __name__ == "__main__":
    # Parse arguments
    args = parse_args()

    # Check if output path is valid
    path = Path(args.output_path)
    parent_directory = path.parent
    if not parent_directory.exists():
        logger.warning("Output path does not exist.")
        logger.info("Creating output directory...")
        parent_directory.mkdir(parents=True, exist_ok=True)
        logger.info("Output directory created.")
    else:
        logger.warning("Output path already exists. Overwriting...")

    if not args.output_path.endswith(".xlsx"):
        logger.error("Output path must end with '.xlsx'.")
        exit(1)

    # Load data from JSON file
    data = load_data(args.file_path)

    # Extract "Applications" data from the JSON file
    data_applications = data["Applications"]
    data_applications = [
        app
        for app in data_applications
        if app["DelegatedPermissions"]
        or app["ApplicationPermissions"]
        or app["MemberOf"]
    ]

    # Extract "Roles" data from the JSON file
    data_user_roles = data["Roles"]
    data_user_roles = [app for app in data_user_roles if app["NumMembers"] != 0]

    application_permissions = process_dataframe(
        data_applications, **applications_permissions_params, isApplicationData=True
    )
    delegated_permissions = process_dataframe(
        data_applications, **delegated_params, isApplicationData=True
    )
    applications_roles = process_dataframe(
        data_applications, **application_roles_params, isApplicationData=True
    )

    summary = create_summary(
        applications_permissions=application_permissions,
        delegated_permissions=delegated_permissions,
        applications_roles=applications_roles,
        rename_map=general_application_parameters,
    )

    user_roles = process_dataframe(
        data_user_roles, **user_roles_params, isApplicationData=False
    )

    logger.info("Writing data to Excel file...")
    with pd.ExcelWriter(args.output_path, engine="xlsxwriter") as writer:
        (summary.to_excel(writer, sheet_name="apps_summary", index=False),)
        (
            application_permissions.to_excel(
                writer, sheet_name="apps_permissions", index=False
            ),
        )
        (
            delegated_permissions.to_excel(
                writer, sheet_name="apps_delegated_permissions", index=False
            ),
        )
        applications_roles.to_excel(writer, sheet_name="apps_roles", index=False)
        user_roles.to_excel(writer, sheet_name="user_roles", index=False)
    logger.info("Data successfully parse to Excel format.")
