import PyUber
import pandas as pd
import numpy as np
import os
import re
import warnings
from pandas.io.formats.style import Styler
from datetime import datetime

# Set Display Options for Pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
pd.options.display.width = 0

# suppress warnings from SQL queries
warnings.simplefilter(action='ignore', category=UserWarning)

RUN_MODE = "PRODUCTION"

# Create path variables for testing / debugging
if RUN_MODE == "DEVELOPMENT":
    out_path = "\\\\AZSHFS.intel.com\\AZAnalysis$\\1274_MAODATA\\Config\\wet_etch\\KNST\\configs\\OperGrid\\Testing\\"
    output_dir = r"//AZSHFS.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/KNST/Script Output/OperGrid/Testing/"
    html_output_dir = r"//AZSHFS.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/KNST/Script Output/OperGrid/Testing/Output_HTML/"
    html_out_file = "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/KNST/Script Output/OperGrid/Testing/Output_HTML/"

    # Dev
    # out_path = "\\\\AZSHFS.intel.com\\AZAnalysis$\\1274_MAODATA\\Config\\wet_etch\\KNST\\configs\\OperGrid\\"
    debug_path = "\\\\AZSHFS.intel.com\\AZAnalysis$\\1274_MAODATA\\wet_etch\\KNST\\Script Output\\OperGrid\\Debugging\\"

else:
    output_dir = r"//AZSHFS.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/KNST/Script Output/OperGrid/"
    html_output_dir = r"//AZSHFS.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/KNST/Script Output/OperGrid/Output_HTML/"
    html_out_file = "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/KNST/Script Output/OperGrid/Output_HTML/"


# Configuring Directories for Web Pages
bootstrap_css = "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/Config/wet_etch/KNST/configs/Bootstrap/bootstrap5_dist/css/bootstrap.min.css"
bootstrap_js = "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/Config/wet_etch/KNST/configs/Bootstrap/bootstrap5_dist/js/bootstrap.bundle.js"
datatables_dir = "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/Config/wet_etch/KNST/configs/DataTables_Plugin/"
# datatables_plugin = "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/Config/wet_etch/KNST/configs/DataTables_Plugin/datatables.min.js"
# datatables_bootstrap_plugin = "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/Config/wet_etch/KNST/configs/DataTables_Plugin/Datatables-1.13.5/css/dataTables.bootstrap5.min.css"
# jquery = "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/Config/wet_etch/KNST/configs/DataTables_Plugin/jQuery-3.7.0/jquery-3.7.0.min.js"
datatables_plugin = datatables_dir + "datatables.min.js"
datatables_bootstrap_plugin = datatables_dir + "Datatables-1.13.5/css/dataTables.bootstrap5.min.css"
jquery = datatables_dir + "jQuery-3.7.0/jquery-3.7.0.min.js"
fixed_columns_js = datatables_dir + "FixedColumns-4.3.0/js/dataTables.fixedColumns.min.js"
fixed_columns_bs_js = datatables_dir + "FixedColumns-4.3.0/js/fixedColumns.bootstrap5.min.js"
fixed_columns_css = datatables_dir + "FixedColumns-4.3.0/css/fixedColumns.dataTables.min.css"
fixed_columns_bs_css = datatables_dir + "FixedColumns-4.3.0/css/fixedColumns.bootstrap5.min.css"

ceid_list = ['NSTwa', 'NSTwn', 'KSTwa', 'NSTsc']


# worker functions to simplify backend code
def map_model(ceid: str) -> str:
    '''
    Returns the corresponding modelname for a given CEID.
    Only configured for NSTwa, NSTwn, and KSTwa modelnames. (NST_F3, NST_WN_F3, KST_F3, NST_SC_F3)

    Args:
        ceid (str): The CEID value to be mapped

    Returns:
        str: The modelname for the CEID value
    '''
    model_ceid_map = {
        'NSTwa': 'NST_F3',
        'NSTwn': 'NST_WN_F3',
        'KSTwa': 'KST_F3',
        'NSTsc': 'NST_SC_F3'
    }
    return model_ceid_map[ceid]


def query_db(db_num: int) -> pd.DataFrame:
    """
    Wrapper function to query the corresponding database with built-in SQL code. \n
    1 = AM_ENTRY \n
    2 = AM_F3_STATUS \n
    3 = FSUI_XEUS \n
    4 = AM_TOOL_FILTER \n
    5 = ENT_STATUS_SPR_MOQR \n
    6 = ENT_STATUS_PARENT_CC \n
    7 = ENTITY_OPERATIONS \n
    8 = ENTITY_LOT_HISTORY \n
    9 = CT_FILE list from (2) \n

    Args:
        db_num (int): Database number to grab data from

    Returns:
        pd.DataFrame: Pandas DataFrame storing database information
    """
    conn = PyUber.connect('F32_PROD_XEUS')
    if db_num == 1:
        sql1 = """
                SELECT 
                    am8.am_ldr_path AS am_ldr_path
                    ,am8.am_ldr_process AS am_ldr_process
                    ,am8.am_ldr_modelname AS am_ldr_modelname
                    ,am8.row_order AS row_order
                    ,am8.entity AS entity
                    ,am8.intro_type AS intro_type
                    ,am8.path AS path
                    ,am8.modelname AS model_name
            FROM 
            F_AM_Entry am8
            WHERE
                        am8.intro_type = 'Production' 
            AND      (am8.modelname LIKE  'KST_F3'
            OR am8.modelname LIKE 'NST_F3'
            OR am8.modelname LIKE 'NST_WN_F3'
            OR am8.modelname LIKE 'NST_SC_F3'
            ) 
        """
        df = pd.read_sql(sql1, conn)
    elif db_num == 2:
        sql2 = """
            SELECT 
                process AS process
                ,modelname AS modelname
                ,objectname AS objectname
                ,row_order AS row_order
                ,entity AS entity
                ,product AS product
                ,route AS route
                ,operation AS operation
                ,recipe_name AS recipe_name
                ,ct_file AS ct_file
                ,GET_ATTRIBUTE_VALUE ( parameter_list , Upper('CAB_LIST'), ';') AS CAB_LIST
                ,process_node AS process_node
        FROM
        (
        SELECT  
                am5.am_ldr_process AS process
                ,am5.am_ldr_modelname AS modelname
                ,am5.am_ldr_objectname AS objectname
                ,am5.row_order AS row_order
                ,am5.entity AS entity
                ,am5.product AS product
                ,am5.route AS route
                ,am5.operation AS operation
                ,am5.recipe_name AS recipe_name
                ,am5.ct_file AS ct_file
                ,am5.parameter_list AS parameter_list
                ,REPLACE(REGEXP_SUBSTR(';'||am5.parameter_list , '(?<=;_PROCESS=).*?(?=(;[^;]+=)|(;$))',1,1,'i'),',',';') AS process_node
        FROM 
        F_AM_F3 am5
        WHERE
        (am5.am_ldr_modelname LIKE  'KST_F3'
        OR am5.am_ldr_modelname LIKE 'NST_F3'
        OR am5.am_ldr_modelname LIKE 'NST_WN_F3'
        OR am5.am_ldr_modelname LIKE 'NST_SC_F3'
        ) 
        AND      am5.ct_file != '*'
        )
        ORDER BY
                    4 Asc
        """
        df = pd.read_sql(sql2, conn)
        df = df.loc[df['OBJECTNAME'] == 'F3_SETUP']
        df["PROCESS_NODE"] = df["PROCESS_NODE"].astype(str)
    elif db_num == 3:
        sql3 = """
            SELECT 
                table_name AS table_name
                ,row_number AS row_number
                ,column_name AS column_name
                ,Max(column_data) AS column_data
        FROM
        (
        SELECT  
                z0.table_name AS table_name
                ,z0.row_number AS row_number
                ,z0.column_name AS column_name
                ,z0.column_data AS column_data
        FROM 
        F_FSUI z0
        WHERE
                    z0.table_name = 'ASOM_OPER_TO_STRING2' 
        AND      (z0.column_name LIKE  'OperList%'
        OR z0.column_name LIKE 'StringOperName%'
        ) 
        )
        GROUP BY 
                table_name
                ,row_number
                ,column_name
        """
        df = pd.read_sql(sql3, conn)
        df = df.pivot(index='ROW_NUMBER', columns='COLUMN_NAME', values='COLUMN_DATA')
    elif db_num == 4:
        sql4 = """
        SELECT 
                am7.am_ldr_process AS process
                ,am7.am_ldr_modelname AS model_name
                ,am7.row_order AS row_order
                ,am7.operation AS operation
                ,am7.route AS route
                ,am7.entity AS entity
                ,Replace(Replace(Replace(Replace(Replace(Replace(am7.tool_allowed,',',';'),chr(9),' '),chr(10),' '),chr(13),' '),chr(34),''''),chr(7),' ') AS tool_allowed
                ,REGEXP_SUBSTR( ';'||am7.parameter_list , '(?<=;LAYER=).*?(?=(;[^;]+=)|(;$))',1,1,'i') AS layer
                ,Replace(Replace(Replace(Replace(Replace(Replace(am7.comments,',',';'),chr(9),' '),chr(10),' '),chr(13),' '),chr(34),''''),chr(7),' ') AS comments
        FROM 
        F_AM_ToolFilter am7
        WHERE
                    (am7.am_ldr_modelname LIKE  'NST_F3'
        OR am7.am_ldr_modelname LIKE 'KST_F3'
        OR am7.am_ldr_modelname LIKE 'NST_WN_F3'
        OR am7.am_ldr_modelname LIKE 'NST_SC_F3'
        ) 
        ORDER BY
                3 Asc
        """
        df = pd.read_sql(sql4, conn)
    elif db_num == 5:
        sql5 = """
        SELECT 
                e.entity AS entity
                ,e.facility AS facility
                ,e.ceid AS ceid
                ,Replace(Replace(Replace(Replace(Replace(Replace(e.configured_processes,',',';'),chr(9),' '),chr(10),' '),chr(13),' '),chr(34),''''),chr(7),' ') AS configured_processes
                ,ea.attribute_name AS attribute_name
                ,ea.attribute_value AS attribute_value
        FROM 
        F_ENTITY e
        LEFT JOIN F_ENTITYATTRIBUTE ea ON ea.entity = e.entity AND ea.history_deleted_flag='N'
        WHERE
                    e.entity_deleted_flag = 'N' 
        AND      (ea.attribute_name LIKE  'MOQRestrict%'
        OR ea.attribute_name LIKE 'AdhocMon90%'
        ) 
        AND      e.configured_processes Like '%' 
        AND      (e.entity LIKE  'KST___'
        OR e.entity LIKE 'NST___'
        ) 
        """
        df = pd.read_sql(sql5, conn)
        df = df.pivot(index='ENTITY', columns='ATTRIBUTE_NAME', values='ATTRIBUTE_VALUE')
    elif db_num == 6:
        sql6 = """
            SELECT 
                facility AS facility
                ,parent_entity AS parent_entity
                ,Replace(Replace(Replace(Replace(Replace(Replace(configured_processes,',',';'),chr(9),' '),chr(10),' '),chr(13),' '),chr(34),''''),chr(7),' ') AS configured_processes
                ,CASE WHEN  entity =  parent_entity THEN 'Parent'
        WHEN   entity like '%MPC1' THEN 'MPC01'
        WHEN   entity like '%MPC2' THEN 'MPC02'
        WHEN   entity like '%MPC3' THEN 'MPC03'
        WHEN   entity like '%MPC4' THEN 'MPC04'
        WHEN   entity like '%MPC5' THEN 'MPC05'
        WHEN   entity like '%MPC6' THEN 'MPC06'
        WHEN   entity like '%MPC7' THEN 'MPC07'
        WHEN   entity like '%MPC8' THEN 'MPC08'
        WHEN   entity like '%MPC9' THEN 'MPC09'
        WHEN   entity like '%MPC10' THEN 'MPC10'
        WHEN   entity like '%MPC11' THEN 'MPC11'
        WHEN   entity like '%MPC12' THEN 'MPC12'
        ELSE   SUBSTR( entity ,8)  END AS subentity
                ,state AS state
                ,availability AS availability
        FROM
        (
        SELECT  
                e.entity AS entity
                ,e.facility AS facility
                ,e.parent_entity AS parent_entity
                ,e.ceid AS ceid
                ,e.configured_processes AS configured_processes
                ,e.state AS state
                ,e.availability AS availability
        FROM 
        F_ENTITY e
        WHERE
                    e.entity_deleted_flag = 'N' 
        AND      e.configured_processes Like '%' 
        AND      (e.entity LIKE  'KST%'
        OR e.entity LIKE 'NST%'
        ) 
        AND      e.entity Not Like '%LP%' 
        )
        """
        df = pd.read_sql(sql6, conn)
    elif db_num == 7:
        sql7 = """
            SELECT 
                eo.facility AS facility
                ,eo.entity AS entity
                ,e.parent_entity AS parent_entity
                ,eo.operation AS operation
                ,To_Char(eo.associate_date,'yyyy-mm-dd hh24:mi:ss') AS associate_date
                ,eo.latest_flag AS entity_oper_latest_flag
        FROM 
        F_EntityOper eo
        LEFT JOIN F_Entity e ON e.entity = eo.entity AND e.facility = eo.facility
        WHERE
                    (eo.entity LIKE  'KST%'
        OR eo.entity LIKE 'NST%'
        ) 
        AND      eo.latest_flag = 'Y' 
        AND      eo.entity Not Like '%LP%' 
        AND      eo.entity Not Like '%MPC%'
        """
        df = pd.read_sql(sql7, conn)
    elif db_num == 8:
        sql8 = """
        SELECT 
                o.area AS area
                ,o.module AS module
                ,lrc.operation AS operation
                ,lrc.lot_type AS lot_type
                ,COUNT ( lrc.lot ) OVER (PARTITION BY  lrc.operation  ) AS four_week_lot_outs
                ,lrc.route_base_name AS route
        FROM 
        F_LOT_RUN_CARD lrc
        INNER JOIN F_Operation O ON o.operation=lrc.operation AND o.facility = lrc.facility AND o.latest_version = 'Y'
        WHERE
                    lrc.out_date >= TRUNC(SYSDATE) - 28 
        AND      (o.module LIKE  '%NST'
        OR o.module LIKE '%NST%'
        OR o.module LIKE '%KST%'
        OR o.module LIKE '%SST%'
        ) 
        """
        df = pd.read_sql(sql8, conn)
        df.drop_duplicates(ignore_index=True, inplace=True)
    elif db_num == 9:
        sql9 = """
        SELECT 
                process AS process
                ,modelname AS modelname
                ,objectname AS objectname
                ,row_order AS row_order
                ,entity AS entity
                ,route AS route
                ,operation AS operation
                ,recipe_name AS recipe_name
                ,ct_file AS ct_file
                ,GET_ATTRIBUTE_VALUE ( parameter_list , Upper('CAB_LIST'), ';') AS CAB_LIST
        FROM
        (
        SELECT  
                am5.am_ldr_process AS process
                ,am5.am_ldr_modelname AS modelname
                ,am5.am_ldr_objectname AS objectname
                ,am5.row_order AS row_order
                ,am5.entity AS entity
                ,am5.route AS route
                ,am5.operation AS operation
                ,am5.recipe_name AS recipe_name
                ,am5.ct_file AS ct_file
                ,am5.parameter_list AS parameter_list
        FROM 
        F_AM_F3 am5
        WHERE
        (am5.am_ldr_modelname LIKE  'KST_F3'
        OR am5.am_ldr_modelname LIKE 'NST_F3'
        OR am5.am_ldr_modelname LIKE 'NST_WN_F3'
        OR am5.am_ldr_modelname LIKE 'NST_SC_F3'
        ) 
        AND      am5.ct_file != '*' 
        )
        ORDER BY
                    4 Asc
        """
        df = pd.read_sql(sql9, conn)
        df = df.loc[df['OBJECTNAME'] == 'CT_CABINET', ['PROCESS', 'MODELNAME', 'OBJECTNAME', 'CT_FILE', 'CAB_LIST']]
    else:
        raise NotImplementedError('This database number is not configured!')
    return df


# worker functions to create dictionaries to store information
def create_route_dict(df: pd.DataFrame) -> dict:
    """Returns a nested dictionary of CEIDs, routes, and their corresponding operations from F3_SETUP: {ceid : {route : set of ops}}

    Arguments:
        pd.DataFrame: F3_SETUP query to grab information

    Returns:
        dict: Nested dictionary storing route <-> operation info
    """
    ceid_routes = {}

    # inner function to add sub-dictionary for each CEID
    def add_routes(ceid: str) -> dict:
        """Worker function to create a dictionary of routes mapped to a set of operations for a given CEID

        Args:
            ceid (str): CEID value to find route information from

        Returns:
            dict: Stores a set of operations for a given route
        """
        route_dict = {}
        new_df = df[(df['MODELNAME'] == map_model(ceid)) & (df['ROUTE'] != '*')]
        for route in {el for list_ in new_df['ROUTE'].str.split('|') for el in list_}:
            test = set(new_df.loc[new_df['ROUTE'].str.contains(route, regex=False)]['OPERATION'].values)
            route_dict.setdefault(route, test)
        return route_dict

    # putting final route dictionary together
    for ceid in ceid_list:
        ceid_routes[ceid] = add_routes(ceid)

    return ceid_routes


def create_ct_file_dict(df: pd.DataFrame) -> dict:
    """Returns a nested dictionary of CEIDs, ct_files, and their corresponding operations from F3_SETUP: {ceid : {ct_file : set of ops}}

    Arguments:
        pd.DataFrame: F3_SETUP query to grab information from

    Returns:
        dict: Nested dictionary storing ct_files <-> operation info
    """
    ceid_ct_files = {}

    # inner function to add sub-dictionary for each CEID
    def add_ct_files(ceid: str) -> dict:
        """Worker function to create a dictionary of ct_files mapped to a set of operations for a given CEID

        Args:
            ceid (str): CEID value to find ct_file information from

        Returns:
            dict: Stores a set of operations for a given ct_file
        """
        ct_file_dict = {}
        new_df = df.loc[df['MODELNAME'] == map_model(ceid)]
        for ct_file in new_df['CT_FILE'].values:
            # if ct_file == 'ct_nocab': continue
            if ct_file == 'ct_k':
                ct_file_dict.setdefault(ct_file, 'DIW')
                continue
            test = set(new_df.loc[new_df['CT_FILE'] == ct_file]['OPERATION'].values)
            ct_file_dict.setdefault(ct_file, test)
        return ct_file_dict

    # putting final route dictionary together
    for ceid in ceid_list:
        ceid_ct_files[ceid] = add_ct_files(ceid)

    return ceid_ct_files


def create_tool_dict(entry_df: pd.DataFrame, ent_stat_df: pd.DataFrame) -> dict:
    """Creates a dictionary of CEIDs to their list of unbagged tools using the entry table database.

    Args:
        entry_df (pd.DataFrame): Entry database info passed as a Pandas DataFrame
        ent_stat_df (pd.DataFrame): Entity Status database info passed as Pandas DataFrame

    Returns:
        dict: map of CEIDs to their corresponding tools as a list {ceid : [tool]}
    """
    ceid_tools = {}

    # creating inner function to add and sort tool lists to ceid_tools
    def add_tools(ceid: str, entities: list, entity_string: str) -> None:
        """Adds the list of tools to the ceid_tools dictionary in numerical order.

        Args:
            ceid (str): CEID for tool list to be added to dictionary
            entities (list): list of tools to be added to dictionary
            entity_string (str): original string of entities to be compared in the entry table
        """
        # checks the modelname for entity_string before adding it to ceid_tools
        if entry_df['MODEL_NAME'].loc[entry_df['ENTITY'] == entity_string].iloc[0] == map_model(ceid):
            if ceid_tools.setdefault(ceid, entities) != entities: ceid_tools[ceid].extend(entities)
            ceid_tools[ceid] = sorted(ceid_tools[ceid])

    # splitting string of entities based on their format
    for entity_string in entry_df['ENTITY']:
        if 'NST(' in entity_string:
            tools = [('NST' + id) for id in entity_string[4:-1].split('|')]
        else:
            tools = entity_string.split('|')

        add_tools('NSTwa', tools, entity_string)
        add_tools('NSTwn', tools, entity_string)
        add_tools('KSTwa', tools, entity_string)
        add_tools('NSTsc', tools, entity_string)
        # add_tools('NSTpc', tools, entity_string)

    # check through each tool list to remove any bagged tools
    for ceid in ceid_tools.keys():
        unbagged_tools = []
        for tool in ceid_tools[ceid]:
            if_not_in_ent_stat = (tool not in ent_stat_df['PARENT_ENTITY'].values)
            if_bagged = 'Bagged' in (ent_stat_df['STATE'].loc[(ent_stat_df['SUBENTITY'] == 'Parent') &
                                                              (ent_stat_df['PARENT_ENTITY'] == tool)].to_string())
            if not ((if_not_in_ent_stat) or (if_bagged)): unbagged_tools.append(tool)
        ceid_tools[ceid] = unbagged_tools

    return ceid_tools


def create_oper_dict(setup_df: pd.DataFrame, lot_hist_df: pd.DataFrame) -> dict:
    """Returns a nested dictionary of CEIDs, operations, and their corresponding recipe names, ct_files, routes: {ceid : {oper : (recipe, ct_file, route)}}

    Arguments:
        setup_df (pd.DataFrame): F3_SETUP table as a Pandas DataFrame query
        lot_hist_df (pd.DataFrame): Lot History database as a Pandas DataFrame query

    Returns:
        dict: Nested dictionary storing operation information.
    """
    ceid_oper = {}

    # inner function to locate the operation lists for each CEID
    def find_oper_list(ceid: str) -> dict:
        """Returns a dictionary of operations mapped to a tuple of their recipe, ct_file, and route
        Duplicate operation numbers denoted with "_#" at the end.
        Current operations are determined with lot_hist_df.

        Args:
            ceid (str): CEID value used to find operations in setup_df

        Returns:
            dict: a dict of operations mapped to a tuple of their recipe name and ct_file
        """
        oper_list = {}
        # slice setup_df with relevant info and tools
        new_df_cols = ['ROW_ORDER', 'ENTITY', 'PRODUCT', 'ROUTE', 'OPERATION', 'RECIPE_NAME', 'CT_FILE']
        # new_df = setup_df.loc[
        #     (setup_df['MODELNAME'] == map_model(ceid)), new_df_cols]
        new_df = setup_df.loc[
            (setup_df['MODELNAME'] == map_model(ceid)) & (setup_df['ENTITY'].str.contains('\\*')), new_df_cols]
        for idx in range(new_df.shape[0]):
            oper = new_df['OPERATION'].iloc[idx]
            rec = new_df['RECIPE_NAME'].iloc[idx]
            ct_file = new_df['CT_FILE'].iloc[idx]
            route = new_df['ROUTE'].iloc[idx]
            prod = new_df['PRODUCT'].iloc[idx]

            # check to see if op is currently running
            if (oper not in lot_hist_df['OPERATION'].values) or (route != '*') or (prod != '*'): continue
            # if (route != '*') or (prod != '*'): continue

            oper_list.setdefault(oper, (rec, ct_file, route, prod))

            # check for duplicate ops in list

            if oper_list[oper] != (rec, ct_file, route, prod):
                count = 2
                if '_' in oper:
                    count = int(oper[-1]) + 1

                oper = oper + '_' + str(count)

            oper_list.setdefault(oper, (rec, ct_file, route, prod))

        return oper_list

    for ceid in ceid_list:
        ceid_oper[ceid] = find_oper_list(ceid)

        print(ceid_oper[ceid])

    return ceid_oper


# worker functions to carry out each check
def check_ops_to_ent(oper: str, entity: str, ops_ent_df: pd.DataFrame, cc_df: pd.DataFrame) -> str:
    """Check to see if op-to-entity association passed in system

    Args:
        oper (str): Input operation to check
        entity (str): Input entity to check
        ops_ent_df (pd.DataFrame): Entity Operation database as a Pandas DataFrame query
        cc_df (pd.DataFrame): Entity Status database with CC info as Pandas Dataframe query

    Returns:
        str: Empty if passed, O if not passed
    """
    # slice DataFrames based on input operation and tool
    new_oe_df = ops_ent_df[(ops_ent_df['OPERATION'] == oper) & (ops_ent_df['PARENT_ENTITY'] == entity)]
    new_cc_df = cc_df[(cc_df['PARENT_ENTITY'] == entity) & (~cc_df['SUBENTITY'].str.contains('MPC'))]

    # compare ops/ent DF with all subentities listed in cc_df
    for subentity in new_cc_df['SUBENTITY']:
        check_str = entity
        if subentity == 'Parent':
            continue
        else:
            check_str += '_' + subentity

        # check if subentity or parent exists in ops/ent DF or not
        if check_str not in new_oe_df['ENTITY'].values: return "O"
    return ''


def check_tool_filter(oper: str, entity: str, tf_df: pd.DataFrame, ceid: str, ceid_ct_files: pd.DataFrame,
                      ceid_routes: pd.DataFrame) -> str:
    """Check to see if op/ent combo is filtered out on AMCT Tool Filter

    Args:
        oper (str): Input operation to check
        entity (str): Input entity to check
        tf_df (pd.DataFrame): Tool Filter database as a Pandas DataFrame query
        ceid (str): CEID used to query tool filter by
        ceid_ct_files (pd.DataFrame): backend list storing ct_file <-> oper info
        ceid_routes (pd.DataFrame): backend list storing route <-> oper info

    Returns:
        str: Empty if passed, A if locked out, S if SIF
    """
    mapped_model = map_model(ceid)
    final_status = ''
    new_df = tf_df.loc[
        tf_df['MODEL_NAME'] == mapped_model, ['ROW_ORDER', 'OPERATION', 'ROUTE', 'ENTITY', 'LAYER', 'TOOL_ALLOWED']]

    # still losing my mind
    for idx in range(new_df.shape[0]):
        curr_row = new_df.iloc[idx].iloc[0]
        curr_oper = new_df.iloc[idx].iloc[1]
        curr_route = new_df.iloc[idx].iloc[2]
        curr_entities = new_df.iloc[idx].iloc[3]
        curr_layer = new_df.iloc[idx].iloc[4]
        curr_status = new_df.iloc[idx].iloc[5]

        # stop loop once final tool open is reached
        # if ('*74.*' in curr_route) or ('*78.*' in curr_route): break

        # check for initial default lockout (row order 1) or 1272 open
        if (curr_row == 1) or ('*72.*' in curr_route): continue

        # split entity and operation strings into sets
        if 'NST(' in curr_entities:
            curr_entities = set('NST' + id for id in curr_entities[4:-1].split('|'))
        elif curr_entities != '*':
            curr_entities = set(curr_entities.split('|'))
        if curr_oper != '*': curr_oper = set(curr_oper.split('|'))

        # oper and entity checks
        in_both = (entity in curr_entities) and (oper in curr_oper)
        in_all_tools = (oper in curr_oper) and (curr_entities == '*')
        in_all_ops = (entity in curr_entities) and (curr_oper == '*')

        # layer check for ops
        if (curr_layer == '*'):
            if (in_both or in_all_tools or in_all_ops) and (curr_route == '*'):
                final_status = curr_status
                # print(f'{in_both} is 1, {in_all_tools} is 2, {in_all_ops} is 3')
                break
        elif (curr_layer != '*') and (in_both or in_all_tools or in_all_ops) and (curr_route == '*'):
            char_list = [x for x in curr_layer.split('*')[1:-1][0]]
            for char in char_list:
                ct_file_lookup = {k: v for k, v in ceid_ct_files[ceid].items() if char in k[2:]}
                oper_set = {s for set_ in ct_file_lookup.values() for s in set_}
                if oper in oper_set:
                    final_status = curr_status
                    # print(f'second break for {oper} and {entity}')
                    break
            else:
                continue
            break

        # route check for ops
        if (curr_route != '*') and (in_both or in_all_tools or in_all_ops):
            route_list = curr_route.split('|')
            for route in route_list:
                if route.endswith('*'): route = route[:-1]
                route_lookup = {k: v for k, v in ceid_routes[ceid].items() if route in k}
                if route_lookup == {}: continue
                oper_set = {s for set_ in route_lookup.values() for s in set_}
                if oper in oper_set:
                    final_status = curr_status
                    break
            else:
                continue
            break

    if final_status == 'FALSE':
        return 'A'
    elif final_status == '=HAS_SIF':
        return 'S'
    return ''


def check_moqr(oper: str, entity: str, asom: pd.DataFrame, ent_stat_df: pd.DataFrame) -> str:
    """Check to see if operation is MOQ restricted on entity

    Args:
        oper (str): Input operation to check
        entity (str): Input entity to check
        asom (pd.DataFrame): FSUI database as a Pandas DataFrame query
        ent_stat_df (pd.DataFrame): Entity Status database with MOQR strings as Pandas DataFrame query

    Returns:
        str: Empty if passed, M if restricted
    """
    try:
        ent_moqr = ent_stat_df.loc[entity].iloc[1].split('/')
    except AttributeError:
        ent_moqr = []

    # check if operation is in MOQR string from entity_status
    if oper in ent_moqr:
        return 'M'

    # check if operation listed in ASOM database
    for string in ent_moqr:
        # skip over anything not listed in ASOM
        if (string.isdigit()) or (string not in asom['StringOperName'].values): continue

        if oper in asom['OperList'].loc[asom['StringOperName'] == string].values[0]: return 'M'
    return ''


def check_parent_cc(oper: str, entity: str, df_list: list, ceid: str, ceid_oper: dict, op_ent_status: str) -> str:
    """Check to see parent or CC status is down

    Args:
        oper (str): Input operation to check
        entity (str): Input entity to check
        df_list (list): list of Pandas DataFrame queries [entity status, ct_files]
        ceid (str): CEID to filter out dataframes by
        ceid_oper (dict): backend dictionary to find operations for a CEID
        op_ent_status (str): backend check from op-to-ent association

    Returns:
        str: Empty if both passed, D if parent down, C if CCs for oper are down
    """
    final_status = ''
    ent_stat_df = df_list[0]
    ct_df = df_list[1]

    tool_df = ent_stat_df.loc[ent_stat_df['PARENT_ENTITY'] == entity]

    # check for parent status
    parent_status = tool_df.loc[tool_df['SUBENTITY'] == 'Parent'].iloc[0].iloc[-1]
    if (parent_status != 'Up'):
        final_status += 'D'

    # early return if ops/ent check fails
    if 'O' in op_ent_status: return final_status

    # early return if ct_file has no CC associated
    ct_file = ceid_oper[ceid][oper][1]
    if ct_file == 'ct_k': return final_status

    # check for CC status from ct_file
    try:
        cc_list = ct_df.loc[ct_df['CT_FILE'] == ct_file, ['CAB_LIST']].iloc[0].iloc[0].split(',')
    except:
        cc_list = []

    cc_status = ''
    for cc in cc_list:
        # print(tool_df.loc[tool_df['SUBENTITY'] == cc, ['AVAILABILITY']].iloc[0].iloc[0])
        try:
            availability = tool_df.loc[tool_df['SUBENTITY'] == cc, ['AVAILABILITY']].iloc[0].iloc[0]
        except IndexError:
            availability = 'Up'
        if availability == 'Down': cc_status = 'C'

    if final_status != "" and cc_status != "":
        return final_status + "|" + cc_status

    return (final_status + cc_status)


def check_spr(entity: str, spr_df: pd.DataFrame) -> str:
    """Check to see if tool flagged for SPR lockouts

    Args:
        entity (str): Input entity to be checked
        spr_df (pd.DataFrame): Entity Status with SPR LO info as Pandas DataFrame query

    Returns:
        str: Empty if passed, R if locked out
    """
    if int(spr_df['AdhocMon90'].loc[entity]) > 0: return 'R'
    return ''


def check_min_spin(entity: str, ent_stat_df: pd.DataFrame) -> str:
    """Check to see if the minimum number of spins are met for entity

    Args:
        entity (str): Input entity to be checked
        ent_stat_df (pd.DataFrame): Entity Status with MPC status as Pandas DataFrame query

    Returns:
        str: Empty if passed, N if not passed
    """
    # slice input DF query based on parent_entity and 'MPC' subentities only
    new_df = ent_stat_df[['PARENT_ENTITY', 'SUBENTITY', 'STATE', 'AVAILABILITY']][
        (ent_stat_df['SUBENTITY'].str.contains('MPC')) & (ent_stat_df['PARENT_ENTITY'] == entity)]

    # count the number of chambers currently up on entity
    count = 0
    for spin_status in new_df['AVAILABILITY']:
        if spin_status == 'Up': count += 1

    # check if min up count is >= 6
    if int(count) <= int(5): return 'N'
    return ''


# Creating Dictionary to hold color values
colors = {
    "bad": "#ffc7ce",
    "neutral": "#ffeb9c",
    "good": "#c6efce",
    "blue": "#9BC2E6",
    "grey": "#A6A6A6",
}


# Create Framework for Writing Output HTML Files
def style_cells(val):
    if re.search(re.compile(r"[ADCNM]"), str(val)):
        props = f"background-color:{colors['bad']}; font-weight:bold;"
    elif re.match(re.compile("O"), str(val)):
        props = f"background-color:{colors['grey']}; font-weight:bold;"
    elif re.search(re.compile(r"[SR]"), str(val)):
        props = f"background-color:{colors['neutral']}; font-weight:bold;"
    else:
        props = f"background-color:{colors['good']}; font-weight:bold;"

    return props


def style_cells_diffs(val):
    if re.search(re.compile(r"[ADCNM]"), str(val)):
        props = f"background-color:{colors['bad']}; font-weight:bold; border-right: 15px solid black;"
    elif re.match(re.compile("O"), str(val)):
        props = f"background-color:{colors['grey']}; font-weight:bold; border-right: 15px solid black;"
    elif re.search(re.compile(r"[SR]"), str(val)):
        props = f"background-color:{colors['neutral']}; font-weight:bold; border-right: 15px solid black;"
    else:
        props = f"background-color:{colors['good']}; font-weight:bold; border-right: 15px solid black;"

    return props


# Custom CSS
css = """
<style>
h1 {
    margin: 20px 10px;
}

td {
    border: 1px solid;
}

th, td { 
    white-space: nowrap;
    text-align: center; 
    /* line-height: 12px; */
}

div.dataTables_wrapper {
    width: 90%;
    margin: 0 auto;
}

.table-div {
    width: 90%;
    margin-left: auto;
    margin-right: auto;
    padding-top: 10px;
}

.body-div {
    width: 90%;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 10px;
}

.table-head {
    margin: 10px;
}

.table-caption {
    margin: 10px;
}

.critical{
    color: red;
    font-weight: bold;
}
</style>
"""

legend_list = """
<div class="body-div">
    <h2><strong>LEGEND:</strong></h2>
</div>
<div class="body-div">
    <ul>
        <li>
            A = AMCT Tool Filter Lockout
        </li>
        <li>
            D = Parent Entity Down
        </li>
        <li>
            C = CC Requirements Not Met For CT File
        </li>
        <li>
            N = Min Chamber Check Not Met (at least 6 chambers UTP)
        </li>
        <li>
            M = MOQ Restricted
        </li>
        <li>
            O = Operation-To-Entity Check Failed
        </li>
        <li>
            S = SIF Only
        </li>
        <li>
            R = SPR Lockout
        </li>
    </ul>
</div>
"""

legend_table = f"""
<div class="body-div">
    <h4><strong>LEGEND:</strong></h2>
</div>
<div class="body-div">
    <table class="table_legend" id="T_legend">
        <tr>

            <td class="data" style="background-color:{colors['bad']}; font-weight: bold">
                A = AMCT Tool Filter Lockout <br>
                D = Parent Entity Down <br>
                C = CC Requirements Not Met For CT File <br>
                N = Min Chamber Check Not Met (at least 6 chambers UTP) <br>
                M = MOQ Restricted
            </td>

            <td class="data" style="background-color:{colors['neutral']}; font-weight: bold">
                S = SIF Only <br>
                R = SPR Lockout
            </td>
        </tr>
        <tr>

            <td class="data" style="background-color:{colors['grey']}; font-weight: bold">
                O = Operation-To-Entity Check Failed
            </td>

            <td class="data" style="background-color:{colors['good']}; font-weight: bold">
                OPEN
            </td>
        </tr>

    </table>
</div>
"""


# <td style="width: 100px; background-color:{colors['bad']}"></td>
# <td style="width: 100px; background-color:{colors['neutral']}"></td>
# <td style="width: 100px; background-color:{colors['grey']}"></td>
# <td style="width: 100px; background-color:{colors['good']}"></td>
# <nav class="navbar navbar-expand-lg bg-body-tertiary"> # --- Previous Nav Class ---


def write_html_output(link_dict, custom_css, searchable=True, **kwargs):
    # home_link = link_dict["home"]
    kst_link = link_dict["kst_href"]
    nstwa_link = link_dict["nstwa_href"]
    nstwn_link = link_dict["nstwn_href"]
    nstsc_link = link_dict["nstsc_href"]
    oper_grid_diffs_link = link_dict["oper_grid_diffs_href"]
    title = kwargs["title"]
    heading = kwargs["heading"]
    table = kwargs["table"]
    body_text = kwargs["body_text"]
    file_name = kwargs["file_name"]
    table_id = kwargs["table_id"]
    caption = kwargs["caption"]
    output_file = html_output_dir + file_name
    updated_date = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')
    data_tables_options = """{
            fixedColumns: {
                left: 2
            },
            paging: true,
            scrollY: "45vh", 
            scrollX: true, 
            pageLength: 100, 
            order: [1, 'asc'], 
            scrollResize: true,
            ordering: true,
            iDisplayLength: -1,
            bStateSave: false,
            aLengthMenu: [[10,25,50,100,-1], [10,25,50,100,"All"]],
        }"""

    if searchable:
        custom_script = f"""
        <script>
        new DataTable("#T_{table_id}", {data_tables_options});
        </script>
        """
    else:
        custom_script = ""

    if "table_head" in kwargs.keys():
        table_head = kwargs["table_head"]
    else:
        table_head = ""

    html_text = f"""

    <!DOCTYPE html>
    <html lang="en">

        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="{bootstrap_css}">
            <link rel="stylesheet" href="{datatables_bootstrap_plugin}">
            <link rel="stylesheet" href="{fixed_columns_css}">
            <link rel="stylesheet" href="{fixed_columns_bs_css}">
            {custom_css}
            <title>{title}</title>
        </head>

        <body>
        <nav class="navbar border-bottom border-body navbar-expand-lg" data-bs-theme="dark" style="background-color: #8EA9DB">
          <div class="container-fluid">
            <div class="collapse navbar-collapse" id="navbarSupportedContent">
              <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item">
                  <a class="navbar-brand" href="{kst_link}">KST</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{nstwa_link}">NSTwa/wp</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{nstwn_link}">NSTwn/pn</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{nstsc_link}">NSTsc</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{oper_grid_diffs_link}">Oper Grid Changes</a>
                </li>
              </ul>
              <span class="navbar-text">Updated: {updated_date}</span>
            </div>
          </div>
        </nav>
        <h1>{heading}</h1>
        <div class="body-div">
            {body_text}
        </div>
        <div class="table-div">
            <div class="table-head">
                <h3>{table_head}</h3>
            </div>
                {table}
            <div class="table-caption">
                <p>{caption}</p>
            </div>
        </div>
        <script src="{bootstrap_js}"></script>
        <script src="{jquery}"></script>
        <script src="{datatables_plugin}"></script>
        <script src="{fixed_columns_js}"></script>
        <script src="{fixed_columns_bs_js}"></script>
        {custom_script}
        </body>
        <footer>
        </footer>
    </html>

    """
    with open(output_file + ".html", "w") as report:
        report.write(html_text)


def write_email_html_output(link_dict, custom_css, **kwargs):
    filename = kwargs.get("file_name", "DEFAULT")
    output_file = html_output_dir + filename
    title = kwargs.get("title")
    heading = kwargs.get("heading")
    body_text = kwargs.get("body_text", "")
    oper_grid_link = link_dict.get("kst_href", "")
    kst_table = kwargs.get("kst_table")
    nst_table = kwargs.get("nst_table")
    nstwn_table = kwargs.get("nstwn_table")
    nstsc_table = kwargs.get("nstsc_table")
    kst_table_head = kwargs.get("kst_table_head", "")
    nst_table_head = kwargs.get("nst_table_head", "")
    nstwn_table_head = kwargs.get("nstwn_table_head", "")
    nstsc_table_head = kwargs.get("nstsc_table_head", "")
    kst_table_caption = kwargs.get("kst_table_caption", "")
    nst_table_caption = kwargs.get("nst_table_caption", "")
    nstwn_table_caption = kwargs.get("nstwn_table_caption", "")
    nstsc_table_caption = kwargs.get("nstsc_table_caption", "")
    updated_date = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')

    html_text = f"""

    <!DOCTYPE html>
    <html lang="en">

        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="{bootstrap_css}">
            {custom_css}
            <title>{title}</title>
        </head>

        <body>
        <h1>{heading}</h1>
        <div class="body-div">
            <p>Updated: {updated_date}</p>
            <a href="{oper_grid_link}">KNST Oper Grid</a>
        </div>
        <div class="body-div">
            {body_text}
        </div>
        <div class="table-div">
            <div class="table-head">
                <h3>{kst_table_head}</h3>
            </div>
                {kst_table}
            <div class="table-caption">
                <p>{kst_table_caption}</p>
            </div>
        </div>
        <div class="table-div">
            <div class="table-head">
                <h3>{nst_table_head}</h3>
            </div>
                {nst_table}
            <div class="table-caption">
                <p>{nst_table_caption}</p>
            </div>
        </div>
        <div class="table-div">
            <div class="table-head">
                <h3>{nstwn_table_head}</h3>
            </div>
                {nstwn_table}
            <div class="table-caption">
                <p>{nstwn_table_caption}</p>
            </div>
        </div>
        <div class="table-div">
            <div class="table-head">
                <h3>{nstsc_table_head}</h3>
            </div>
                {nstsc_table}
            <div class="table-caption">
                <p>{nstsc_table_caption}</p>
            </div>
        </div>
        <script src="{bootstrap_js}"></script>
        </body>
        <footer>
        </footer>
    </html>

    """
    with open(output_file + ".html", "w") as report:
        report.write(html_text)


def write_diffs_html_output(link_dict, custom_css, searchable=True, **kwargs):
    filename = kwargs.get("file_name", "DEFAULT")
    output_file = html_output_dir + filename
    title = kwargs.get("title")
    heading = kwargs.get("heading")
    kst_link = link_dict.get("kst_href", "")
    nstwa_link = link_dict.get("nstwa_href", "")
    nstwn_link = link_dict.get("nstwn_href", "")
    nstsc_link = link_dict.get("nstsc_href", "")
    oper_grid_diffs_link = link_dict.get("oper_grid_diffs_href", "")
    changes_detected = kwargs.get("changes_detected", False)
    if changes_detected:
        body_text = kwargs.get("body_text", "")
    else:
        body_text = """<h2><strong>No Changes Detected</strong></h2>"""

    kst_table = kwargs.get("kst_table")
    nst_table = kwargs.get("nst_table")
    nstwn_table = kwargs.get("nstwn_table")
    nstsc_table = kwargs.get("nstsc_table")
    kst_table_head = kwargs.get("kst_table_head", "")
    nst_table_head = kwargs.get("nst_table_head", "")
    nstwn_table_head = kwargs.get("nstwn_table_head", "")
    nstsc_table_head = kwargs.get("nstsc_table_head", "")
    kst_table_caption = kwargs.get("kst_table_caption", "")
    nst_table_caption = kwargs.get("nst_table_caption", "")
    nstwn_table_caption = kwargs.get("nstwn_table_caption", "")
    nstsc_table_caption = kwargs.get("nstsc_table_caption", "")
    updated_date = datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')
    table_ids = kwargs.get("table_ids", [])
    data_tables_options = """{
                fixedColumns: {
                    left: 1
                },
                paging: true,
                scrollY: "20vh", 
                scrollX: true, 
                pageLength: 10, 
                order: [0, 'asc'], 
                scrollResize: true,
                ordering: true,
                iDisplayLength: -1,
                bStateSave: false,
                aLengthMenu: [[10,25,50,100,-1], [10,25,50,100,"All"]],
            }"""

    custom_script = ""
    if searchable:
        for table_id in table_ids:
            custom_script += f"""
                <script>
                new DataTable("#T_{table_id}", {data_tables_options});
                </script>
                """
    else:
        custom_script = ""

    html_text = f"""

    <!DOCTYPE html>
    <html lang="en">

        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <link rel="stylesheet" href="{bootstrap_css}">
            <link rel="stylesheet" href="{datatables_bootstrap_plugin}">
            <link rel="stylesheet" href="{fixed_columns_css}">
            <link rel="stylesheet" href="{fixed_columns_bs_css}">
            {custom_css}
            <title>{title}</title>
        </head>

        <body>

        <nav class="navbar border-bottom border-body navbar-expand-lg" data-bs-theme="dark" style="background-color: #8EA9DB">
          <div class="container-fluid">
            <div class="collapse navbar-collapse" id="navbarSupportedContent">
              <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                <li class="nav-item">
                  <a class="navbar-brand" href="{kst_link}">KST</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{nstwa_link}">NSTwa/wp</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{nstwn_link}">NSTwn/pn</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{nstsc_link}">NSTsc</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{oper_grid_diffs_link}">Oper Grid Changes</a>
                </li>
              </ul>
              <span class="navbar-text">Updated: {updated_date}</span>
            </div>
          </div>
        </nav>
        <h1>{heading}</h1>
        <div class="body-div">
            {body_text}
        </div>
        <div class="table-div">
            <div class="table-head">
                <h3>{kst_table_head}</h3>
            </div>
                {kst_table}
            <div class="table-caption">
                <p>{kst_table_caption}</p>
            </div>
        </div>
        <div class="table-div">
            <div class="table-head">
                <h3>{nst_table_head}</h3>
            </div>
                {nst_table}
            <div class="table-caption">
                <p>{nst_table_caption}</p>
            </div>
        </div>
        <div class="table-div">
            <div class="table-head">
                <h3>{nstwn_table_head}</h3>
            </div>
                {nstwn_table}
            <div class="table-caption">
                <p>{nstwn_table_caption}</p>
            </div>
        </div>
        <div class="table-div">
            <div class="table-head">
                <h3>{nstsc_table_head}</h3>
            </div>
                {nstsc_table}
            <div class="table-caption">
                <p>{nstsc_table_caption}</p>
            </div>
        </div>
        <script src="{bootstrap_js}"></script>
        <script src="{jquery}"></script>
        <script src="{datatables_plugin}"></script>
        <script src="{fixed_columns_js}"></script>
        <script src="{fixed_columns_bs_js}"></script>
        {custom_script}
        </body>
        <footer>
        </footer>
    </html>

    """
    with open(output_file + ".html", "w") as report:
        report.write(html_text)


# running program
def main():
    # query all needed databases once
    print('Querying databases...')
    df1 = query_db(1)
    df2 = query_db(2)
    df3 = query_db(3)
    df4 = query_db(4)
    df5 = query_db(5)
    df6 = query_db(6)
    df7 = query_db(7)
    df8 = query_db(8)
    df9 = query_db(9)

    if RUN_MODE == "DEVELOPMENT":
        for idx, tbl in enumerate([df1, df2, df3, df4, df5, df6, df7, df8, df9]):
            tbl.to_csv(debug_path + f"df{idx + 1}" + ".csv")

    # create backend data structures for later reference
    print('Creating backend data structures...')
    ceid_tools = create_tool_dict(df1, df6)

    ceid_oper = create_oper_dict(df2, df8)

    ceid_routes = create_route_dict(df2)

    ceid_ct_files = create_ct_file_dict(df2)


    # worker function to create data structure
    def create_data_dict() -> dict:
        """Create nested dictionary to store status information

        |O| = op-to-entity association

        |A| = tool filter lockout

        |S| = SIF

        |M| = MOQ restriction

        |D| = parent status

        |C| = CC status

        |R| = SPR lockout

        |N| = minimum spin count (>= 6)

        Returns:
            dict: Nested dict in format: {ceid : {op : {entity : status}}}
        """
        op_ent_data = {}

        for ceid in ceid_tools.keys():
            op_ent_data[ceid] = {}
            for oper in ceid_oper[ceid]:
                op_ent_data[ceid][oper] = {}
                for tool in ceid_tools[ceid]:
                    check_1 = check_ops_to_ent(oper, tool, df7, df6)
                    check_2 = check_tool_filter(oper, tool, df4, ceid, ceid_ct_files, ceid_routes)
                    check_3 = check_moqr(oper, tool, df3, df5)
                    check_4 = check_parent_cc(oper, tool, [df6, df9], ceid, ceid_oper, check_1)
                    check_5 = check_spr(tool, df5)
                    check_6 = check_min_spin(tool, df6)
                    op_ent_data[ceid][oper][tool] = '|'.join(
                        [x for x in [check_1, check_2, check_3, check_4, check_5, check_6] if x != ''])

        return op_ent_data

    # worker function to unpack data into DataFrame format
    def unpack_data(ceid: str, op_ent_data: dict, ct_df: pd.DataFrame, ceid_oper: dict) -> pd.DataFrame:
        """Unpack nested dictionary into ops grid format as DataFrame.
        Adds additional columns to count number of open op/ent paths, recipe names, CCs used, and routes.

        Args:
            ceid (str): CEID to display ops grid
            op_ent_data (dict): backend nested dict storing all status info
            ct_df (pd.DataFrame): F3_SETUP table with CT_FILE info as Pandas DataFrame query
            ceid_oper (dict): backend dictionary storing recipe, CC, and route info from oper

        Returns:
            pd.DataFrame: Returns the BEAUTIFUL ops grid as a Pandas DataFrame
        """
        # extract data for given CEID
        curr_data = op_ent_data[ceid]
        ops_list = curr_data.keys()
        rec_list = []
        cc_list = []
        route_list = []
        paths_open_list = []

        # create columns to be added to ops grid
        for op in ops_list:
            paths_open = 0

            rec_list.append(ceid_oper[ceid][op][0])
            route_list.append(ceid_oper[ceid][op][2])

            ct_file = ceid_oper[ceid][op][1]
            if ct_file == 'ct_k':
                cc = 'DIW'
            else:
                try:
                    cc = ct_df['CAB_LIST'][ct_df['CT_FILE'] == ct_file].iloc[0]
                except:
                    cc = ""
            cc_list.append(cc)

            for tool in op_ent_data[ceid][op].keys():
                if op_ent_data[ceid][op][tool] == '': paths_open += 1

            paths_open_list.append(paths_open)

        # assemble DataFrame from dictionary
        out_df = pd.DataFrame.from_dict(curr_data, orient='index')
        out_df['Recipe'] = rec_list
        out_df['CC Used'] = cc_list
        # out_df['Route'] = route_list
        out_df.insert(0, 'Paths Open', paths_open_list)
        out_df.sort_values('Paths Open', inplace=True)
        out_df.index.name = 'Operation'
        out_df.reset_index()

        return out_df

    # worker function to find any grid updates between each iteration
    def check_updates(grid: pd.DataFrame, path: os.PathLike, ceid: str) -> list:
        """Compares the current grid with the previous grid version.
        Returns a list of DataFrames showing the highlighted differences and changes to the list of running operations and tools.

        Args:
            grid (pd.DataFrame): Current version of the grid after newest run of queries.
            path (os.PathLike): File path to old grid iteration.

        Returns:
            list: Nested list storing (added) and (removed) operations and tools
        """
        # check if there is an old grid to compare with
        if not (os.path.isfile(path)): return []

        # extract grids with common columns for initial row comparisons
        old_grid = pd.read_csv(path, sep='\t', index_col=0)

        if grid.equals(old_grid):
            dummy_df = pd.DataFrame()
            dummy_df.to_csv(output_dir + f'{ceid}_diffs.tab')
            return []
        grid["Operation"] = grid["Operation"].astype(int)
        old_grid["Operation"] = old_grid["Operation"].astype(int)
        intercol = grid.columns.intersection(old_grid.columns)
        interrow = set(np.intersect1d(grid.Operation.values, old_grid.Operation.values))
        new_g1 = grid.loc[:, intercol]
        new_g2 = old_grid.loc[:, intercol]

        # produce new DataFrame with highlighted differences
        diff_df = pd.merge(new_g2, new_g1, on=['Operation'], how='outer', suffixes=('_old', '_new')) \
            .set_index(['Operation'])
        diff_df.columns = pd.MultiIndex.from_tuples(diff_df.columns.str.split('_').map(tuple)) \
            .swaplevel()
        diff_df = diff_df['new'].compare(diff_df['old'])
        diff_df.rename(columns={'self': 'New', 'other': 'Old'}, level=-1, inplace=True)
        if diff_df.shape[0] == 0:
            dummy_df = pd.DataFrame()
            dummy_df.to_csv(output_dir + f'{ceid}_diffs.tab')
            return []

        # find any added/removed tools and operations
        removed_cols = [col for col in old_grid.columns if col not in intercol]
        added_cols = [col for col in grid.columns if col not in intercol]
        removed_ops = [str(op) for op in old_grid.Operation.values if op not in interrow]
        added_ops = [str(op) for op in grid.Operation.values if op not in interrow]

        # save differences to .tab file
        diffspath = output_dir + f'{ceid}_diffs.tab'
        diff_df.columns = ["_".join(a) for a in diff_df.columns.to_flat_index()]

        for col in diff_df.columns:
            if "Paths" in col:
                diff_df[col] = diff_df[col].fillna(0).astype({col: "int32"})
            if "Recipe" in col or "CC Used" in col or "Paths" in col:
                diff_df.drop(col, inplace=True, axis=1)

        diff_df.to_csv(diffspath, sep='\t')
        return [removed_cols, added_cols, removed_ops, added_ops]

    # iterating through all op/ent combinations to create ops grid info
    print('Creating Ops Grid information...')
    op_ent_data = create_data_dict()

    # checking previous grid iterations...
    for ceid in ceid_list:

        if os.path.exists(output_dir + f'{ceid}_diffs.tab'):
            print(f"Removing previous Difference Log for {ceid}...")
            os.remove(output_dir + f'{ceid}_diffs.tab')

        print(f"Checking for changes to {ceid} Oper Grid...")
        output_path = output_dir + f'{ceid}_ops_grid.tab'
        temp_path = output_dir + f'{ceid}_ops_grid_temp.tab'

        # using a temporary copy of the grid for reformatting
        ops_grid = unpack_data(ceid, op_ent_data, df9, ceid_oper)
        ops_grid.to_csv(temp_path, sep='\t')
        ops_grid = pd.read_csv(temp_path, sep='\t')
        changes = check_updates(ops_grid, output_path, ceid)
        if changes != []:
            rcols = changes[0]
            acols = changes[1]
            rrows = changes[2]
            arows = changes[3]
            if rcols != []:
                rcols = ','.join(rcols)
                print(f'Removed tools: {rcols} from {ceid}')
            if acols != []:
                acols = ','.join(acols)
                print(f'Added tools: {acols} from {ceid}')
            if rrows != []:
                rrows = ','.join(rrows)
                print(f'Removed operations: {rrows} from {ceid}')
            if arows != []:
                arows = ','.join(arows)
                print(f'Added operations: {arows} from {ceid}')
        else:
            print("No Changes Detected")
        os.remove(temp_path)

    # reformatting data into DataFrame structure
    print('Formatting the Ops Grids...')
    KST_ops_grid = unpack_data('KSTwa', op_ent_data, df9, ceid_oper).reset_index()
    KST_ops_grid = KST_ops_grid.merge(df2[["OPERATION", "PROCESS_NODE"]], how="inner", left_on="Operation",
                                      right_on="OPERATION")
    KST_ops_grid.drop(["OPERATION"], axis=1, inplace=True)

    NST_WN_ops_grid = unpack_data('NSTwn', op_ent_data, df9, ceid_oper).reset_index()
    NST_WN_ops_grid = NST_WN_ops_grid.merge(df2[["OPERATION", "PROCESS_NODE"]], how="inner", left_on="Operation",
                                            right_on="OPERATION")
    NST_WN_ops_grid.drop(["OPERATION"], axis=1, inplace=True)

    NST_ops_grid = unpack_data('NSTwa', op_ent_data, df9, ceid_oper).reset_index()
    NST_ops_grid = NST_ops_grid.merge(df2[["OPERATION", "PROCESS_NODE"]], how="inner", left_on="Operation",
                                      right_on="OPERATION")
    NST_ops_grid.drop(["OPERATION"], axis=1, inplace=True)

    NST_SC_ops_grid = unpack_data('NSTsc', op_ent_data, df9, ceid_oper).reset_index()
    NST_SC_ops_grid = NST_SC_ops_grid.merge(df2[["OPERATION", "PROCESS_NODE"]], how="inner", left_on="Operation",
                                            right_on="OPERATION")
    NST_SC_ops_grid.drop(["OPERATION"], axis=1, inplace=True)

    # Create Lists of Entities for Subset Parameter
    kst_subset = [x for x in KST_ops_grid.columns if re.match("KST", x)]
    nstwn_subset = [x for x in NST_WN_ops_grid.columns if re.match("NST", x)]
    nst_subset = [x for x in NST_ops_grid.columns if re.match("NST", x)]
    nstsc_subset = [x for x in NST_SC_ops_grid.columns if re.match("NST", x)]

    # saving ops grid to .csv files in output directory
    print('Saving the New Ops Grid as .tab files...')
    KST_ops_grid.to_csv(output_dir + 'KST_ops_grid.tab', sep='\t')
    NST_ops_grid.to_csv(output_dir + 'NSTwa_ops_grid.tab', sep='\t')
    NST_WN_ops_grid.to_csv(output_dir + 'NSTwn_ops_grid.tab', sep='\t')
    NST_SC_ops_grid.to_csv(output_dir + 'NSTsc_ops_grid.tab', sep='\t')

    # Generate Report HTML Tables from Dataframes
    print("Creating Report HTML Tables...")
    df_kst_report = Styler(KST_ops_grid,
                           table_attributes="class='table table-striped cell-borders' style='width: 100%'",
                           na_rep=" ") \
        .map(style_cells, subset=kst_subset) \
        .hide(axis="index") \
        .to_html(table_uuid="kst")

    df_nstwa_report = Styler(NST_ops_grid,
                             table_attributes="class='table table-striped' style='width: 100%'",
                             na_rep=" ") \
        .map(style_cells, subset=nst_subset) \
        .hide(axis="index") \
        .to_html(table_uuid="nstwa")

    df_nstwn_report = Styler(NST_WN_ops_grid,
                             table_attributes="class='table table-striped' style='width: 100%'",
                             na_rep=" ") \
        .map(style_cells, subset=nstwn_subset) \
        .hide(axis="index") \
        .to_html(table_uuid="nstwn")

    df_nstsc_report = Styler(NST_SC_ops_grid,
                             table_attributes="class='table table-striped' style='width: 100%'",
                             na_rep=" ") \
        .map(style_cells, subset=nstsc_subset) \
        .hide(axis="index") \
        .to_html(table_uuid="nstsc")


    # Creating Difference Reports
    print("Checking for Differences in Oper Grids...")
    df_kst_diffs = pd.read_csv(output_dir + "KST_diffs.tab", sep="\t")
    df_nst_diffs = pd.read_csv(output_dir + "NSTwa_diffs.tab", sep="\t")
    df_nstwn_diffs = pd.read_csv(output_dir + "NSTwn_diffs.tab", sep="\t")
    df_nstsc_diffs = pd.read_csv(output_dir + "NSTsc_diffs.tab", sep="\t")

    # Create Lists of Entities for Subset Parameter
    if len(df_kst_diffs) != 0:
        kst_diff_subset = [x for x in df_kst_diffs.columns if re.match("KST", x)]
        kst_diff_check = [x for x in kst_diff_subset if "Old" in x]
    else:
        kst_diff_subset = []
        kst_diff_check = []
    if len(df_nst_diffs) != 0:
        nst_diff_subset = [x for x in df_nst_diffs.columns if re.match("NST", x)]
        nst_diff_check = [x for x in nst_diff_subset if "Old" in x]
    else:
        nst_diff_subset = []
        nst_diff_check = []
    if len(df_nstwn_diffs) != 0:
        nstwn_diff_subset = [x for x in df_nstwn_diffs.columns if re.match("NST", x)]
        nstwn_diff_check = [x for x in nstwn_diff_subset if "Old" in x]
    else:
        nstwn_diff_subset = []
        nstwn_diff_check = []
    if len(df_nstsc_diffs) != 0:
        nstsc_diff_subset = [x for x in df_nstsc_diffs.columns if re.match("NST", x)]
        nstsc_diff_check = [x for x in nstsc_diff_subset if "Old" in x]
    else:
        nstsc_diff_subset = []
        nstsc_diff_check = []

    if len(df_kst_diffs) == 0 and len(df_nst_diffs) == 0 and len(df_nstwn_diffs) == 0 and len(df_nstsc_diffs) == 0:
        df_changes_detected = pd.DataFrame().reset_index(drop=True)
        changes_detected = False
    else:
        df_changes_detected = pd.DataFrame([{'changes_detected': 'There are Changes Detected'}]).reset_index(drop=True)
        changes_detected = True

    df_changes_detected.to_csv(output_dir + "OperGrid_Changes_Detected.tab", sep="\t")

    print("Creating Difference HTML Tables...")
    df_kst_diff_report = Styler(df_kst_diffs,
                                table_attributes="class='table table-striped cell-borders' style='width: 100%'",
                                na_rep=" ") \
        .map(style_cells, subset=kst_diff_subset) \
        .map(style_cells_diffs, subset=kst_diff_check) \
        .hide(axis="index") \
        .to_html(table_uuid="kst_diffs")

    df_nst_diff_report = Styler(df_nst_diffs,
                                table_attributes="class='table table-striped' style='width: 100%'",
                                na_rep=" ") \
        .map(style_cells, subset=nst_diff_subset) \
        .map(style_cells_diffs, subset=nst_diff_check) \
        .hide(axis="index") \
        .to_html(table_uuid="nstwa_diffs")

    df_nstwn_diff_report = Styler(df_nstwn_diffs,
                                  table_attributes="class='table table-striped' style='width: 100%'",
                                  na_rep=" ") \
        .map(style_cells, subset=nstwn_diff_subset) \
        .map(style_cells_diffs, subset=nstwn_diff_check) \
        .hide(axis="index") \
        .to_html(table_uuid="nstwn_diffs")

    df_nstsc_diff_report = Styler(df_nstsc_diffs,
                                  table_attributes="class='table table-striped' style='width: 100%'",
                                  na_rep=" ") \
        .map(style_cells, subset=nstsc_diff_subset) \
        .map(style_cells_diffs, subset=nstsc_diff_check) \
        .hide(axis="index") \
        .to_html(table_uuid="nstsc_diffs")

    # Creating Lines Down Reports
    print("Checking for Lines Down Operations...")
    df_kst_ld = KST_ops_grid[KST_ops_grid["Paths Open"] == 0]["Operation"]
    df_nst_ld = NST_ops_grid[NST_ops_grid["Paths Open"] == 0]["Operation"]
    df_nstwn_ld = NST_WN_ops_grid[NST_WN_ops_grid["Paths Open"] == 0]["Operation"]
    df_nstsc_ld = NST_SC_ops_grid[NST_SC_ops_grid["Paths Open"] == 0]["Operation"]

    if len(df_kst_ld) != 0:
        print("KST - Lines Down Operation Detected")
    if len(df_nst_ld) != 0:
        print("NSTwa - Lines Down Operation Detected")
    if len(df_nstwn_ld) != 0:
        print("NSTwn - Lines Down Operation Detected")
    if len(df_nstsc_ld) != 0:
        print("NSTsc - Lines Down Operation Detected")

    if len(df_kst_ld) == 0 and len(df_nst_ld) == 0 and len(df_nstwn_ld) == 0 and len(df_nstsc_ld) == 0:
        df_lines_down = pd.DataFrame().reset_index(drop=True)
    else:
        df_lines_down = pd.DataFrame([{'lines_down': 'There are Operations Lines Down'}]).reset_index(drop=True)

    df_lines_down.to_csv(output_dir + "LinesDown_Operations.tab", sep="\t")

    print("Creating Lines Down HTML Tables...")
    df_kst_ld_report = Styler(df_kst_ld,
                              table_attributes="class='table table-striped cell-borders' style='width: 50px'",
                              na_rep=" ") \
        .hide(axis="index") \
        .to_html(table_uuid="kst_ld")

    df_nst_ld_report = Styler(df_nst_ld,
                              table_attributes="class='table table-striped' style='width: 50px'",
                              na_rep=" ") \
        .hide(axis="index") \
        .to_html(table_uuid="nstwa_ld")

    df_nstwn_ld_report = Styler(df_nstwn_ld,
                                table_attributes="class='table table-striped' style='width: 50px'",
                                na_rep=" ") \
        .hide(axis="index") \
        .to_html(table_uuid="nstwn_ld")

    df_nstsc_ld_report = Styler(df_nstsc_ld,
                                table_attributes="class='table table-striped' style='width: 50px'",
                                na_rep=" ") \
        .hide(axis="index") \
        .to_html(table_uuid="nstsc_ld")

    # Creating HTML Config Dictionaries
    KST_Output_Dict = {
        "title": "KST Oper Grid",
        "heading": "KST Oper Grid",
        "table": df_kst_report,
        "body_text": legend_table,
        "file_name": "KST_OperGrid",
        "table_id": "kst",
        "caption": ""
    }

    NSTWA_Output_Dict = {
        "title": "NSTwa Oper Grid",
        "heading": "NSTwa/wp Oper Grid",
        "table": df_nstwa_report,
        "body_text": legend_table,
        "file_name": "NSTwa_OperGrid",
        "table_id": "nstwa",
        "caption": ""
    }

    NSTWN_Output_Dict = {
        "title": "NSTwn Oper Grid",
        "heading": "NSTwn/pn Oper Grid",
        "table": df_nstwn_report,
        "body_text": legend_table,
        "file_name": "NSTwn_OperGrid",
        "table_id": "nstwn",
        "caption": ""
    }

    NSTSC_Output_Dict = {
        "title": "NSTsc Oper Grid",
        "heading": "NSTsc Oper Grid",
        "table": df_nstsc_report,
        "body_text": legend_table,
        "file_name": "NSTsc_OperGrid",
        "table_id": "nstsc",
        "caption": ""
    }

    DIFFS_DICT = {
        "file_name": "KNST_OperGrid_Diffs",
        "title": "KNST Oper Grid Differences",
        "heading": "KNST Oper Grid Differences",
        "kst_table": df_kst_diff_report,
        "nst_table": df_nst_diff_report,
        "nstwn_table": df_nstwn_diff_report,
        "nstsc_table": df_nstsc_diff_report,
        "body_text": legend_table,
        "caption": "",
        "changes_detected": changes_detected,
        "table_ids": []
    }

    LINES_DOWN_DICT = {
        "file_name": "KNST_Lines_Down_Operations",
        "title": "KNST Lines Down Operations",
        "heading": "KNST Lines Down Operations",
        "kst_table": df_kst_ld_report,
        "nst_table": df_nst_ld_report,
        "nstwn_table": df_nstwn_ld_report,
        "nstsc_table": df_nstsc_ld_report,
        "body_text": "<p>The following operations are Lines Down for the KNST Module: </p>",
        "caption": ""
    }

    # Update DIFFS DICT if DIFF DF's are Empty
    if len(df_kst_diffs) != 0:
        DIFFS_DICT["kst_table_head"] = "KST Oper Grid Deltas:"
        DIFFS_DICT["table_ids"].append("kst_diffs")
    else:
        DIFFS_DICT["kst_table"] = ""
    if len(df_nst_diffs) != 0:
        DIFFS_DICT["nst_table_head"] = "NSTwa Oper Grid Deltas:"
        DIFFS_DICT["table_ids"].append("nstwa_diffs")
    else:
        DIFFS_DICT["nst_table"] = ""
    if len(df_nstwn_diffs) != 0:
        DIFFS_DICT["nstwn_table_head"] = "NSTwn Oper Grid Deltas:"
        DIFFS_DICT["table_ids"].append("nstwn_diffs")
    else:
        DIFFS_DICT["nstwn_table"] = ""
    if len(df_nstsc_diffs) != 0:
        DIFFS_DICT["nstsc_table_head"] = "NSTsc Oper Grid Deltas:"
        DIFFS_DICT["table_ids"].append("nstsc_diffs")
    else:
        DIFFS_DICT["nstsc_table"] = ""

    # Update LINES DOWN DICT if LD DF's are Empty
    if len(df_kst_ld) != 0:
        LINES_DOWN_DICT["kst_table_head"] = "KST Lines Down Operations:"
    else:
        LINES_DOWN_DICT["kst_table"] = ""
    if len(df_nst_ld) != 0:
        LINES_DOWN_DICT["nst_table_head"] = "NSTwa Lines Down Operations:"
    else:
        LINES_DOWN_DICT["nst_table"] = ""
    if len(df_nstwn_ld) != 0:
        LINES_DOWN_DICT["nstwn_table_head"] = "NSTwn Lines Down Operations:"
    else:
        LINES_DOWN_DICT["nstwn_table"] = ""
    if len(df_nstsc_ld) != 0:
        LINES_DOWN_DICT["nstsc_table_head"] = "NSTsc Lines Down Operations:"
    else:
        LINES_DOWN_DICT["nstsc_table"] = ""

    # Generating Links Dictionary for NavBar
    links = {
        "kst_href": html_out_file + KST_Output_Dict["file_name"] + ".html",
        "nstwa_href": html_out_file + NSTWA_Output_Dict["file_name"] + ".html",
        "nstwn_href": html_out_file + NSTWN_Output_Dict["file_name"] + ".html",
        "nstsc_href": html_out_file + NSTSC_Output_Dict["file_name"] + ".html",
        "oper_grid_diffs_href": html_out_file + DIFFS_DICT["file_name"] + ".html"
    }

    # Writing output HTML Files with Ops Grid
    print("Writing HTML Output Files...")
    # write_html_output(link_dict=links, custom_css=css, searchable=False, **HOME_Output_Dict)
    write_html_output(link_dict=links, custom_css=css, searchable=True, **KST_Output_Dict)
    write_html_output(link_dict=links, custom_css=css, searchable=True, **NSTWA_Output_Dict)
    write_html_output(link_dict=links, custom_css=css, searchable=True, **NSTWN_Output_Dict)
    write_html_output(link_dict=links, custom_css=css, searchable=True, **NSTSC_Output_Dict)

    write_diffs_html_output(link_dict=links, custom_css=css, **DIFFS_DICT)
    write_email_html_output(link_dict=links, custom_css=css, **LINES_DOWN_DICT)


if __name__ == '__main__':
    main()