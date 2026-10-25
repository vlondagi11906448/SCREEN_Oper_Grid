import PyUber
import pandas as pd
import numpy as np
import os
import re
import sys
import warnings
from pandas.errors import EmptyDataError
from pandas.io.formats.style import Styler
from datetime import datetime
from pathlib import Path

# Set Display Options for Pandas
pd.set_option('display.max_columns', None)
pd.set_option('display.max_colwidth', None)
pd.set_option('display.max_rows', None)
pd.options.display.width = 0

# suppress warnings from SQL queries
warnings.simplefilter(action='ignore', category=UserWarning)

# RUN_MODE = DEBUG or PROD - Determines if this is being used for debugging / development and provides
# additional debugging logs
RUN_MODE = "PROD"
# RUN_MODE = "DEBUG"

# To run OperGrid for a different module, change the module selection below in the else block.
# Must be one of the toolset labels configured in the Toolset clas toolset_selection variable
# Currently configured for ["BUR", "KNST", "XST", "XRT"]

if len(sys.argv) > 1:
    module_selection = sys.argv[1]
    print(f"Setting Module Selection: {module_selection}")
else:
    module_selection = "XST"
    print(f"Setting Default Module Selection: {module_selection}")


class DebuggingLogger:
    def __init__(self, run_mode):
        self.dbgpath = Path("C:/Users/vlondagi/source/repos/SCREEN_Oper_Grid/Script_Output/Debugging")
        self.run_mode = run_mode
        self.print_log = self.check_run_mode(self.print_log)
        self.log_df = self.check_run_mode(self.log_df)
        self.log_file = self.dbgpath / "Log_File.txt"

        if not self.log_file.is_file():
            with open(self.log_file, "a") as f:
                pass

    def check_run_mode(self, func):
        def wrapper(*args, **kwargs):
            if self.run_mode == "DEBUG":
                result = func(*args, **kwargs)
            else:
                result = None

            return result

        return wrapper

    def print_log(self, *args, **kwargs):
        log_message = kwargs.get("log_message", "")

        if "log_message" != "":
            print(f"Log Message: {log_message}")
            with open(self.log_file, "a") as f:
                f.write(log_message)
                f.write("\n")

    def log_df(self, *args, **kwargs):
        for idx, arg in enumerate(args):
            if isinstance(arg, pd.DataFrame):
                tbl = f"{arg} + {idx}"
                arg.to_csv(self.dbgpath / tbl, index=False, index_label=None)

        df = kwargs.get("df", "")
        df_name = kwargs.get("df_name", "")
        if not df.empty and isinstance(df, pd.DataFrame) and df_name:
            base_path = self.dbgpath / df_name
            print(f"Logging df: {df_name}")
            df.to_csv(base_path.with_suffix(".csv"), index=False, index_label=None)
            print(f"{df_name} saved")

        dfs = kwargs.get("dfs", "")
        if dfs != "" and isinstance(dfs, list):
            for idx, df in enumerate(dfs):
                base_path = self.dbgpath / f"df{idx}"
                print(f"Logging df{idx}...")
                df.to_csv(base_path.with_suffix(".csv"), index=False, index_label=None)
                print(f"df{idx} saved")
        elif dfs != "" and isinstance(dfs, dict):
            for k, v in dfs.items():
                base_path = self.dbgpath / k
                print(f"Logging {k}...")
                v.to_csv(base_path.with_suffix(".csv"), index=False, index_label=None)
                print(f"{k} saved")


dbg = DebuggingLogger(run_mode=RUN_MODE)


class Toolset:
    def __init__(self, toolset):
        self.toolset = toolset
        self.toolset_selection = ["BUR", "KNST", "XST", "XRT"]
        self.model_map = {}
        self.path_variables = {}
        self.lot_hist_filter = {}
        self.attributes = []
        self.recipe_col = ''

        if self.toolset == "BUR":
            self.min_chamber_check = 2
            self.attributes = ["AdhocMon90", "MOQRestrict"]
            self.recipe_col = "recipe_name"
        elif self.toolset == "KNST":
            self.min_chamber_check = 6
            self.attributes = ["AdhocMon90", "MOQRestrict"]
            self.recipe_col = "recipe_name"
        elif self.toolset == "XST":
            self.min_chamber_check = 2
            self.attributes = ["AdhocMon90", "MOQRestrict"]
            self.recipe_col = "recipe_name"
        elif self.toolset == "XRT":
            self.min_chamber_check = 4
            self.attributes = ["MOQRestrict"]
            self.recipe_col = "recipe"
        else:
            self.min_chamber_check = 6
            self.attributes = ["AdhocMon90", "MOQRestrict"]
            self.recipe_col = 'recipe_name'

    def get_model_map(self):
        if self.toolset not in self.toolset_selection:
            print(f"Invalid Toolset: {self.toolset} not in {self.toolset_selection}")
        elif self.toolset == "BUR":
            self.model_map = {
                'BURcu': 'BUR_CU_F3'
            }
        elif self.toolset == "KNST":
            self.model_map = {
                'NSTwa': 'NST_F3',
                'NSTwn': 'NST_WN_F3',
                'KSTwa': 'KST_F3',
                'NSTsc': 'NST_SC_F3'
            }
        elif self.toolset == "XST":
            self.model_map = {
                'SST': 'SST_F3',
                'EST': 'EST_F3',
                'GST': 'GST_F3_SCNET',
                'EST53': 'EST_F3_SCNET_NSD'
            }
        elif self.toolset == "XRT":
            self.model_map = {
                'DRTnb': 'DRT_FE_BV_F3',
                'DRTnc': 'DRT_FE_F3',
                'DRTcb': 'DRT_BE_BV_F3',
                'DRTcu': 'DRT_BE_F3'
            }
        else:
            print(f"Invalid Toolset")

    def get_path_variables(self):
        self.path_variables.update({
                "bootstrap_css":
                    "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/Config/wet_etch/KNST/configs/Bootstrap/bootstrap5_dist/css/bootstrap.min.css",
                "bootstrap_js":
                    "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/Config/wet_etch/KNST/configs/Bootstrap/bootstrap5_dist/js/bootstrap.bundle.js",
                "datatables_dir":
                    "https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/Config/wet_etch/KNST/configs/DataTables_Plugin/"
            })
        if RUN_MODE == "DEBUG":
            self.path_variables.update({
                "out_path": Path("C:/Users/vlondagi/source/repos/SCREEN_Oper_Grid/Script_Output"),
                "output_dir": Path("C:/Users/vlondagi/source/repos/SCREEN_Oper_Grid/Script_Output"),
                "html_output_dir": Path("C:/Users/vlondagi/source/repos/SCREEN_Oper_Grid/Script_Output/Output_HTML"),
                "html_out_file": r"C:/Users/vlondagi/source/repos/SCREEN_Oper_Grid/Script_Output/Output_HTML/"
            })
        else:
            if self.toolset not in self.toolset_selection:
                print(f"Invalid Toolset: {self.toolset} not in {self.toolset_selection}")
            elif self.toolset == "BUR":
                self.path_variables.update({
                    "output_dir": Path(
                        "//azshfs.intel.com/AZAnalysis$/1278_MAODATA/Wet_Etch/BUR/Script_Output/xRT_BUR_Oper_Grid"),
                    "html_output_dir": Path(
                        "//azshfs.intel.com/AZAnalysis$/1278_MAODATA/Wet_Etch/BUR/Script_Output/xRT_BUR_Oper_Grid/Output_HTML"),
                    "html_out_file":r"https://azshweb.intel.com/AZAnalysis$/1278_MAODATA/Wet_Etch/BUR/Script_Output/xRT_BUR_Oper_Grid/Output_HTML/"
                })
            elif self.toolset == "KNST":
                self.path_variables.update({
                    "output_dir": Path("//AZSHFS.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/KNST/Script Output/OperGrid"),
                    "html_output_dir": Path(
                        "//AZSHFS.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/KNST/Script Output/OperGrid/Output_HTML"),
                    "html_out_file": r"https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/KNST/Script Output/OperGrid/Output_HTML/"
                })
            elif self.toolset == "XST":
                self.path_variables.update({
                    "output_dir": Path(
                        "//AZSHFS.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/EST_SST/Script Output/OperGrid"),
                    "html_output_dir": Path(
                        "//AZSHFS.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/EST_SST/Script Output/OperGrid/Output_HTML"),
                    "html_out_file": r"https://azshweb.intel.com/AZAnalysis$/1274_MAODATA/wet_etch/EST_SST/Script Output/OperGrid/Output_HTML/"
                })
            elif self.toolset == "XRT":
                self.path_variables.update({
                    "output_dir": Path(
                        "//azshfs.intel.com/AZAnalysis$/1278_MAODATA/Wet_Etch/BUR/Script_Output/xRT_BUR_Oper_Grid"),
                    "html_output_dir": Path(
                        "//azshfs.intel.com/AZAnalysis$/1278_MAODATA/Wet_Etch/BUR/Script_Output/xRT_BUR_Oper_Grid/Output_HTML"),
                    "html_out_file": r"https://azshweb.intel.com/AZAnalysis$/1278_MAODATA/Wet_Etch/BUR/Script_Output/xRT_BUR_Oper_Grid/Output_HTML/"
                })
            else:
                print(f"Invalid Toolset")

    def get_lot_hist_filter(self):
        if self.toolset not in self.toolset_selection:
            print(f"Invalid Toolset: {self.toolset} not in {self.toolset_selection}")
        elif self.toolset == "BUR":
            self.lot_hist_filter = {
                'BURcu': True
            }
        elif self.toolset == "KNST":
            self.lot_hist_filter = {
                'NSTwa': True,
                'NSTwn': True,
                'KSTwa': False,
                'NSTsc': False
            }
        elif self.toolset == "XST":
            self.lot_hist_filter = {
                'SST': True,
                'EST': True,
                'GST': True,
                'EST53': True
            }
        elif self.toolset == "XRT":
            self.lot_hist_filter = {
                'DRTnb': True,
                'DRTnc': True,
                'DRTcb': True,
                'DRTcu': True
            }
        else:
            print(f"Invalid Toolset")


toolset = Toolset(module_selection)
toolset.get_model_map()
toolset.get_path_variables()
toolset.get_lot_hist_filter()

# Create path variables for testing / debugging

output_dir = toolset.path_variables.get("output_dir", "")
html_output_dir = toolset.path_variables.get("html_output_dir", "")
html_out_file = toolset.path_variables.get("html_out_file", "")
bootstrap_css = toolset.path_variables.get("bootstrap_css", "")
bootstrap_js = toolset.path_variables.get("bootstrap_js", "")
datatables_dir = toolset.path_variables.get("datatables_dir", "")

# Configuring Directories for Web Pages
datatables_plugin = datatables_dir + "datatables.min.js"
datatables_bootstrap_plugin = datatables_dir + "Datatables-1.13.5/css/dataTables.bootstrap5.min.css"
jquery = datatables_dir + "jQuery-3.7.0/jquery-3.7.0.min.js"
fixed_columns_js = datatables_dir + "FixedColumns-4.3.0/js/dataTables.fixedColumns.min.js"
fixed_columns_bs_js = datatables_dir + "FixedColumns-4.3.0/js/fixedColumns.bootstrap5.min.js"
fixed_columns_css = datatables_dir + "FixedColumns-4.3.0/css/fixedColumns.dataTables.min.css"
fixed_columns_bs_css = datatables_dir + "FixedColumns-4.3.0/css/fixedColumns.bootstrap5.min.css"

am_model_map = toolset.model_map

ceid_list = [k for k in am_model_map.keys()]

entity_prefix_map = {ceid: re.match(r'[A-Z]+', ceid).group(0) for ceid in ceid_list}
entity_prefixes = sorted(set(entity_prefix_map.values()))


def get_all_keys(nested_dict):
    keys = []
    for k, v in nested_dict.items():
        keys.append(k)
        if isinstance(v, dict):
            keys.extend(get_all_keys(v))

    return keys


def get_nested_dict_vals(data, search_str, not_in_str: list = []):
    results = []

    if isinstance(data, dict):
        for k, v in data.items():
            if search_str in str(k) and all(search_str not in item for item in not_in_str):
                results.append(v)

            results.extend(get_nested_dict_vals(v, search_str, not_in_str))

    elif isinstance(data, list):
        for item in data:
            results.extend(get_nested_dict_vals(item, search_str, not_in_str))

    return results


# worker functions to simplify backend code
def map_model(ceid: str, model_ceid_map: dict = am_model_map) -> str:
    '''
    Returns the corresponding modelname for a given CEID.
    Only configured for NSTwa, NSTwn, and KSTwa modelnames. (NST_F3, NST_WN_F3, KST_F3, NST_SC_F3)

    Args:
        ceid (str): The CEID value to be mapped

    Returns:
        str: The modelname for the CEID value
    '''

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
        conditions = [f"am8.modelname LIKE '{value}'" for value in am_model_map.values()]
        # ({'\n OR '.join(conditions)})
        sql1 = f"""
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
            AND ({'\n OR '.join(conditions)})
        """
        df = pd.read_sql(sql1, conn)
        dbg.log_df(df=df, df_name="DF1_From_Query")
    elif db_num == 2:
        conditions = [f"am5.am_ldr_modelname LIKE '{value}'" for value in am_model_map.values()]
        sql2 = f"""
            SELECT 
                process AS process
                ,modelname AS modelname
                ,objectname AS objectname
                ,row_order AS row_order
                ,entity AS entity
                ,product AS product
                ,route AS route
                ,operation AS operation
                ,{toolset.recipe_col} AS recipe_name
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
                ,am5.recipe AS recipe
                ,am5.ct_file AS ct_file
                ,am5.parameter_list AS parameter_list
                ,REPLACE(REGEXP_SUBSTR(';'||am5.parameter_list , '(?<=;_PROCESS=).*?(?=(;[^;]+=)|(;$))',1,1,'i'),',',';') AS process_node
        FROM 
        F_AM_F3 am5
        WHERE
        ({'\n OR '.join(conditions)})
        AND      am5.ct_file != '*'
        )
        ORDER BY
                    4 Asc
        """
        df = pd.read_sql(sql2, conn)
        df = df.loc[df['OBJECTNAME'] == 'F3_SETUP']
        df["PROCESS_NODE"] = df["PROCESS_NODE"].astype(str)
        dbg.log_df(df=df, df_name="DF2_From_Query")
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
        dbg.log_df(df=df, df_name="DF3_From_Query")
    elif db_num == 4:
        conditions = [f"am7.am_ldr_modelname LIKE '{value}'" for value in am_model_map.values()]
        sql4 = f"""
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
        ({'\n OR '.join(conditions)})
        ORDER BY
                3 Asc
        """
        df = pd.read_sql(sql4, conn)
        dbg.log_df(df=df, df_name="DF4_From_Query")
    elif db_num == 5:
        conditions = [f"e.entity LIKE '{value}___'" for value in entity_prefixes]
        attributes = [f"ea.attribute_name LIKE '{value}%'" for value in toolset.attributes]
        sql5 = f"""
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
        AND      ({'\n OR '.join(attributes)})
        AND      e.configured_processes Like '%' 
        AND      ({'\n OR '.join(conditions)})
        """
        df = pd.read_sql(sql5, conn)
        df = df.pivot(index='ENTITY', columns='ATTRIBUTE_NAME', values='ATTRIBUTE_VALUE')
        dbg.log_df(df=df, df_name="DF5_From_Query")
    elif db_num == 6:
        conditions = [f"e.entity LIKE '{value}%'" for value in entity_prefixes]
        sql6 = f"""
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
        WHEN   entity like '%MPC13' THEN 'MPC13'
        WHEN   entity like '%MPC14' THEN 'MPC14'
        WHEN   entity like '%MPC15' THEN 'MPC15'
        WHEN   entity like '%MPC16' THEN 'MPC16'
        WHEN   entity like '%U9' THEN 'U9'
        WHEN   entity like '%U10' THEN 'U10'
        WHEN   entity like '%U11' THEN 'U11'
        WHEN   entity like '%U12' THEN 'U12'
        WHEN   entity like '%U13' THEN 'U13'
        WHEN   entity like '%U14' THEN 'U14'
        WHEN   entity like '%U15' THEN 'U15'
        WHEN   entity like '%U16' THEN 'U16'
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
        AND      ({'\n OR '.join(conditions)})
        AND      e.entity Not Like '%LP%' 
        AND      e.entity Not Like '%WPO%' 
        )
        """
        df = pd.read_sql(sql6, conn)
        dbg.log_df(df=df, df_name="DF6_From_Query")
    elif db_num == 7:
        conditions = [f"e.entity LIKE '{value}%'" for value in entity_prefixes]
        sql7 = f"""
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
        WHERE    ({'\n OR '.join(conditions)})
        AND      eo.latest_flag = 'Y' 
        AND      eo.entity Not Like '%LP%' 
        AND      eo.entity Not Like '%MPC%'
        AND      eo.entity Not Like '%SPIN%'
        """
        df = pd.read_sql(sql7, conn)
        dbg.log_df(df=df, df_name="DF7_From_Query")
    elif db_num == 8:
        conditions = [f"o.module LIKE '%{value}%'" for value in entity_prefixes]
        sql8 = f"""
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
        AND      ({'\n OR '.join(conditions)})
        """
        df = pd.read_sql(sql8, conn)
        df.drop_duplicates(ignore_index=True, inplace=True)
        dbg.log_df(df=df, df_name="DF8_From_Query")
    elif db_num == 9:
        conditions = [f"am5.am_ldr_modelname LIKE '{value}'" for value in am_model_map.values()]
        sql9 = f"""
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
        ({'\n OR '.join(conditions)})
        AND      am5.ct_file != '*' 
        )
        ORDER BY
                    4 Asc
        """
        df = pd.read_sql(sql9, conn)
        df = df.loc[df['OBJECTNAME'] == 'CT_CABINET', ['PROCESS', 'MODELNAME', 'OBJECTNAME', 'CT_FILE', 'CAB_LIST']]
        dbg.log_df(df=df, df_name="DF9_From_Query")
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
    ceid_tools = {ceid: [] for ceid in ceid_list}

    def filter_tools(tools: list) -> list:
        cleaned = []
        for tool in tools:
            token = str(tool).strip()
            if token == '' or '*' in token:
                continue
            cleaned.append(token)
        return cleaned

    # creating inner function to add and sort tool lists to ceid_tools
    def add_tools(ceid: str, entities: list, entity_string: str) -> None:
        """Adds the list of tools to the ceid_tools dictionary in numerical order.

        Args:
            ceid (str): CEID for tool list to be added to dictionary
            entities (list): list of tools to be added to dictionary
            entity_string (str): original string of entities to be compared in the entry table
        """
        # checks the modelname for entity_string before adding it to ceid_tool
        # if "*" in entity_string:
        #     entity_string = "|".join(ent_stat_df["PARENT_ENTITY"].unique())

        if entry_df['MODEL_NAME'].loc[entry_df['ENTITY'] == entity_string].iloc[0] == map_model(ceid):
            ceid_tools[ceid].extend(entities)


    # splitting string of entities based on their format
    for entity_string in entry_df['ENTITY']:
        entity_string = str(entity_string).strip()
        match = re.fullmatch(r'([A-Z]+)\(([^)]+)\)', entity_string)
        if match:
            entity_prefix = match.group(1)
            tools = [f"{entity_prefix}{item.strip()}" for item in match.group(2).split('|')]
        else:
            tools = [item.strip() for item in entity_string.split('|') if item.strip()]

        tools = filter_tools(tools)

        for tool in ceid_list:
            add_tools(tool, tools, entity_string)

    for ceid in ceid_list:
        if len(ceid_tools[ceid]) == 0:
            prefix = entity_prefix_map[ceid]
            ceid_tools[ceid] = sorted(ent_stat_df.loc[
                ent_stat_df["PARENT_ENTITY"].str.startswith(prefix), "PARENT_ENTITY"
            ].unique())
        else:
            ceid_tools[ceid] = sorted(set(ceid_tools[ceid]))


    # check through each tool list to remove any bagged tools
    for ceid in ceid_list:
        all_tools = list(ceid_tools[ceid])
        unbagged_tools = []
        for tool in ceid_tools[ceid]:
            if_not_in_ent_stat = (tool not in ent_stat_df['PARENT_ENTITY'].values)
            if_bagged = 'Bagged' in (ent_stat_df['STATE'].loc[(ent_stat_df['SUBENTITY'] == 'Parent') &
                                                              (ent_stat_df['PARENT_ENTITY'] == tool)].to_string())
            if not ((if_not_in_ent_stat) or (if_bagged)): unbagged_tools.append(tool)

        # keep table headers populated even when runtime status marks all tools as bagged
        if len(unbagged_tools) == 0:
            ceid_tools[ceid] = all_tools
        else:
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
        new_df = setup_df.loc[(setup_df['MODELNAME'] == map_model(ceid)), new_df_cols]
        for idx in range(new_df.shape[0]):
            oper = new_df['OPERATION'].iloc[idx]
            rec = new_df['RECIPE_NAME'].iloc[idx]
            ct_file = new_df['CT_FILE'].iloc[idx]
            route = new_df['ROUTE'].iloc[idx]
            prod = new_df['PRODUCT'].iloc[idx]

            # include AMCT defaults; do not limit to only recent lot history
            filt_lot_hist = toolset.lot_hist_filter.get(ceid, True)
            if filt_lot_hist:
                if (oper not in lot_hist_df['OPERATION'].values) or (route != '*') or (prod != '*'):
                    continue
            else:
                if (route != '*') or (prod != '*'):
                    continue

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
def check_ops_to_ent(oper: str, entity: str, ops_ent_df: pd.DataFrame, cc_df: pd.DataFrame,
                     parent_assoc_set: set = None) -> str:
    """Check to see if op-to-entity association passed in system

    Args:
        oper (str): Input operation to check
        entity (str): Input entity to check
        ops_ent_df (pd.DataFrame): Entity Operation database as a Pandas DataFrame query
        cc_df (pd.DataFrame): Entity Status database with CC info as Pandas Dataframe query

    Returns:
        str: Empty if passed, O if not passed
    """
    oper = str(oper).strip().split("_")[0]
    entity = str(entity).strip()

    if parent_assoc_set is not None:
        return '' if (oper, entity) in parent_assoc_set else "O"

    # valid association only when parent entity itself is explicitly associated to the operation
    parent_assoc = ops_ent_df[
        (ops_ent_df['OPERATION'].astype(str).str.strip().split("_")[0] == oper)
        & (ops_ent_df['PARENT_ENTITY'].astype(str).str.strip() == entity)
        & (ops_ent_df['ENTITY'].astype(str).str.strip() == entity)
    ]

    if parent_assoc.empty:
        return "O"

    return ''


def check_tool_filter(oper: str, entity: str, tf_df: pd.DataFrame, ceid: str, ceid_ct_files: pd.DataFrame,
                      ceid_routes: pd.DataFrame, tf_rules: pd.DataFrame = None) -> str:
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
    final_status = ''
    if tf_rules is None:
        mapped_model = map_model(ceid)
        new_df = tf_df.loc[
            tf_df['MODEL_NAME'] == mapped_model, ['ROW_ORDER', 'OPERATION', 'ROUTE', 'ENTITY', 'LAYER', 'TOOL_ALLOWED']]
        new_df["LAYER"] = new_df["LAYER"].fillna("*")
    else:
        new_df = tf_rules

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
        curr_entities = str(curr_entities).strip()
        curr_oper = str(curr_oper).strip()

        if curr_entities != '*':
            match = re.fullmatch(r'([A-Z]+)\(([^)]+)\)', curr_entities)
            if match:
                entity_prefix = match.group(1)
                entity_ids = [item.strip() for item in match.group(2).split('|') if item.strip()]
                curr_entities = {f"{entity_prefix}{entity_id}" for entity_id in entity_ids}
            else:
                curr_entities = {item.strip() for item in curr_entities.split('|') if item.strip()}

        if curr_oper != '*':
            curr_oper = {item.strip() for item in curr_oper.split('|') if item.strip()}

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
    except (AttributeError, KeyError, IndexError, TypeError):
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
    if "AdhocMon90" in spr_df.columns:
        spr_df["AdhocMon90"] = spr_df["AdhocMon90"].fillna(0)
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
             ((ent_stat_df['SUBENTITY'].str.contains('MPC') |
              ent_stat_df['SUBENTITY'].str.contains('SPIN') |
              ent_stat_df['SUBENTITY'].str.contains('U')) &
             (ent_stat_df['PARENT_ENTITY'] == entity))]

    # count the number of chambers currently up on entity
    count = 0
    for spin_status in new_df['AVAILABILITY']:
        if spin_status == 'Up': count += 1

    # check if min up count is >= min_chamber_check
    if int(count) <= int(toolset.min_chamber_check): return 'N'
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

legend_list = f"""
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
            N = Min Chamber Check Not Met (at least {toolset.min_chamber_check} chambers UTP)
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
                N = Min Chamber Check Not Met (at least {toolset.min_chamber_check} chambers UTP) <br>
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


def write_html_output(link_dict, custom_css, searchable=True, **kwargs):
    nav_links = [f'<li class="nav-item">\n\t <a class="navbar-brand" href="{val}">{key.split("_")[0].upper()}</a> \n\t</li>' for key, val in link_dict.items() if "oper" not in str(key)]
    oper_grid_diffs_link = link_dict["oper_grid_diffs_href"]
    oper_lines_down_link = link_dict.get("oper_lines_down_href", "")
    title = kwargs["title"]
    heading = kwargs["heading"]
    table = kwargs["table"]
    body_text = kwargs["body_text"]
    file_name = kwargs["file_name"]
    table_id = kwargs["table_id"]
    caption = kwargs["caption"]
    output_file = html_output_dir / file_name
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
                {"\n".join(nav_links)}
                <li class="nav-item">
                  <a class="navbar-brand" href="{oper_grid_diffs_link}">Oper Grid Changes</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{oper_lines_down_link}">Lines Down</a>
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
    with open(output_file.with_suffix(".html"), "w") as report:
        report.write(html_text)


def write_email_html_output(link_dict, custom_css, **kwargs):
    nav_links = [f'<li class="nav-item">\n\t <a class="navbar-brand" href="{val}">{key.split("_")[0].upper()}</a> \n\t</li>' for key, val in link_dict.items() if "oper" not in str(key)]
    filename = kwargs.get("file_name", "DEFAULT")
    output_file = html_output_dir / filename
    title = kwargs.get("title")
    heading = kwargs.get("heading")
    body_text = kwargs.get("body_text", "")
    oper_grid_link = next(iter(link_dict.values()), None)

    table_div_items = []
    table_divs = []
    for ceid in ceid_list:
        tbl = kwargs.get(f"{ceid}_table")
        head = kwargs.get(f"{ceid}_table_head", "")
        cap = kwargs.get(f"{ceid}_table_caption", "")

        temp = [tbl, head, cap]

        table_div_items.append(temp)

    for div in table_div_items:
        table_div = f"""
            <div class="table-div">
                <div class="table-head">
                    <h3>{div[0]}</h3>
                </div>
                    {div[1]}
                <div class="table-caption">
                    <p>{div[2]}</p>
                </div>
            </div>
        """

        table_divs.append(table_div)

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
            <a href="{oper_grid_link}">Oper Grid</a>
        </div>
        <div class="body-div">
            {body_text}
        </div>
        {"\n".join(table_divs)}
        <script src="{bootstrap_js}"></script>
        </body>
        <footer>
        </footer>
    </html>

    """
    with open(output_file.with_suffix(".html"), "w") as report:
        report.write(html_text)


def write_diffs_html_output(link_dict, custom_css, searchable=True, **kwargs):
    nav_links = [f'<li class="nav-item">\n\t <a class="navbar-brand" href="{val}">{key.split("_")[0].upper()}</a> \n\t</li>' for key, val in link_dict.items() if "oper" not in str(key)]
    filename = kwargs.get("file_name", "DEFAULT")
    output_file = html_output_dir / filename
    title = module_selection + " " + kwargs.get("title")
    heading = kwargs.get("heading")
    oper_grid_diffs_link = link_dict.get("oper_grid_diffs_href", "")
    oper_lines_down_link = link_dict.get("oper_lines_down_href", "")
    changes_detected = kwargs.get("changes_detected", False)
    if changes_detected:
        body_text = kwargs.get("body_text", "")
    else:
        body_text = """<h2><strong>No Changes Detected</strong></h2>"""

    table_div_items = []
    table_divs = []
    for ceid in ceid_list:
        tbl = kwargs.get(f"{ceid}_table")
        head = kwargs.get(f"{ceid}_table_head", "")
        cap = kwargs.get(f"{ceid}_table_caption", "")

        if tbl is not None:
            temp = [tbl, head, cap]

            table_div_items.append(temp)

    for div in table_div_items:
        table_div = f"""
                <div class="table-div">
                    <div class="table-head">
                        <h3>{div[1]}</h3>
                    </div>
                        {div[0]}
                    <div class="table-caption">
                        <p>{div[2]}</p>
                    </div>
                </div>
            """

        table_divs.append(table_div)

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
                {"\n".join(nav_links)}
                <li class="nav-item">
                  <a class="navbar-brand" href="{oper_grid_diffs_link}">Oper Grid Changes</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{oper_lines_down_link}">Lines Down</a>
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
        {"\n".join(table_divs)}
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
    with open(output_file.with_suffix(".html"), "w") as report:
        report.write(html_text)


def write_lines_down_html_output(link_dict, custom_css, searchable=True, **kwargs):
    nav_links = [f'<li class="nav-item">\n\t <a class="navbar-brand" href="{val}">{key.split("_")[0].upper()}</a> \n\t</li>' for key, val in link_dict.items() if "oper" not in str(key)]
    filename = kwargs.get("file_name", "DEFAULT")
    output_file = html_output_dir / filename
    title = module_selection + " " + kwargs.get("title")
    heading = kwargs.get("heading")
    body_text = kwargs.get("body_text", "")
    oper_grid_diffs_link = link_dict.get("oper_grid_diffs_href", "")
    oper_lines_down_link = link_dict.get("oper_lines_down_href", "")
    lines_down_opers = kwargs.get("lines_down_opers", False)
    if lines_down_opers:
        body_text = kwargs.get("body_text", "")
    else:
        body_text = """<h2><strong>No Lines Down Operations Detected</strong></h2>"""

    table_div_items = []
    table_divs = []
    for ceid in ceid_list:
        tbl = kwargs.get(f"{ceid.lower()}_table")
        head = kwargs.get(f"{ceid.lower()}_table_head", "")
        cap = kwargs.get(f"{ceid.lower()}_table_caption", "")

        if tbl not in (None, ""):
            temp = [tbl, head, cap]
            table_div_items.append(temp)

    for div in table_div_items:
        table_div = f"""
                 <div class="table-div">
                     <div class="table-head">
                         <h3>{div[1]}</h3>
                     </div>
                         {div[0]}
                     <div class="table-caption">
                         <p>{div[2]}</p>
                     </div>
                 </div>
            """

        table_divs.append(table_div)

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
                {"\n".join(nav_links)}
                <li class="nav-item">
                  <a class="navbar-brand" href="{oper_grid_diffs_link}">Oper Grid Changes</a>
                </li>
                <li class="nav-item">
                  <a class="navbar-brand" href="{oper_lines_down_link}">Lines Down</a>
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
        {"\n".join(table_divs)}
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
    with open(output_file.with_suffix(".html"), "w") as report:
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

    df_log = {"df1": df1, "df2": df2, "df3": df3,
              "df4": df4, "df5": df5, "df6": df6,
              "df7": df7, "df8": df8, "df9": df9}
    # dbg.log_df(dfs=df_log)


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
        # precompute lookup structures to avoid repeating expensive DataFrame scans per op/tool pair
        parent_assoc_set = {
            (str(op).strip(), str(parent).strip())
            for op, parent, ent in zip(df7['OPERATION'], df7['PARENT_ENTITY'], df7['ENTITY'])
            if str(parent).strip() == str(ent).strip()
        }

        tf_rules_by_ceid = {}
        for ceid in ceid_tools.keys():
            mapped_model = map_model(ceid)
            tf_rules = df4.loc[
                df4['MODEL_NAME'] == mapped_model,
                ['ROW_ORDER', 'OPERATION', 'ROUTE', 'ENTITY', 'LAYER', 'TOOL_ALLOWED']
            ].copy()
            tf_rules['LAYER'] = tf_rules['LAYER'].fillna('*')
            tf_rules_by_ceid[ceid] = tf_rules

        op_ent_data = {}
        for ceid in ceid_tools.keys():
            op_ent_data[ceid] = {}
            for oper in ceid_oper[ceid]:
                op_ent_data[ceid][oper] = {}
                for tool in ceid_tools[ceid]:
                    check_1 = check_ops_to_ent(oper, tool, df7, df6, parent_assoc_set)
                    check_2 = check_tool_filter(oper, tool, df4, ceid, ceid_ct_files, ceid_routes,
                                                tf_rules_by_ceid[ceid])
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
        ops_list = list(curr_data.keys())
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
        out_df.index = out_df.index.astype(str)
        out_df['Recipe'] = pd.Series(rec_list, index=[str(op) for op in ops_list])
        out_df['CC Used'] = pd.Series(cc_list, index=[str(op) for op in ops_list])
        # out_df['Route'] = route_list
        out_df.insert(0, 'Paths Open', pd.Series(paths_open_list, index=[str(op) for op in ops_list]))
        out_df.insert(0, 'Operation', out_df.index)
        out_df.sort_values(['Paths Open', 'Operation'], inplace=True)
        out_df.reset_index(drop=True, inplace=True)

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
        old_grid = pd.read_csv(path, sep='\t')

        # support legacy files that saved Operation as index or unnamed first column
        if "Operation" not in old_grid.columns:
            unnamed_cols = [col for col in old_grid.columns if str(col).lower().startswith('unnamed:')]
            if len(unnamed_cols) != 0:
                old_grid.rename(columns={unnamed_cols[0]: 'Operation'}, inplace=True)
            elif len(old_grid.columns) != 0:
                old_grid.rename(columns={old_grid.columns[0]: 'Operation'}, inplace=True)

        # remove serialized index artifacts from both frames
        grid = grid.loc[:, ~grid.columns.astype(str).str.lower().str.startswith('unnamed:')]
        old_grid = old_grid.loc[:, ~old_grid.columns.astype(str).str.lower().str.startswith('unnamed:')]

        if grid.equals(old_grid):
            dummy_df = pd.DataFrame(columns=["Operation"])
            dummy_df_path = output_dir / f'{ceid}_diffs'
            dummy_df.to_csv(dummy_df_path.with_suffix('.tab'), sep='\t', index=False)
            return []
        grid["Operation"] = pd.to_numeric(grid["Operation"], errors='coerce')
        old_grid["Operation"] = pd.to_numeric(old_grid["Operation"], errors='coerce')
        grid = grid.dropna(subset=["Operation"]).copy()
        old_grid = old_grid.dropna(subset=["Operation"]).copy()
        grid["Operation"] = grid["Operation"].astype('int64').astype(str)
        old_grid["Operation"] = old_grid["Operation"].astype('int64').astype(str)
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
            dummy_df = pd.DataFrame(columns=["Operation"])
            dummy_df_path = output_dir / f'{ceid}_diffs'
            dummy_df.to_csv(dummy_df_path.with_suffix('.tab'), sep='\t', index=False)
            return []

        # find any added/removed tools and operations
        removed_cols = [col for col in old_grid.columns if col not in intercol]
        added_cols = [col for col in grid.columns if col not in intercol]
        removed_ops = [str(op) for op in old_grid.Operation.values if op not in interrow]
        added_ops = [str(op) for op in grid.Operation.values if op not in interrow]

        # save differences to .tab file
        diffspath = output_dir / f'{ceid}_diffs.tab'
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
        pth_ceid_diffs = output_dir / f'{ceid}_diffs'
        if os.path.exists(pth_ceid_diffs.with_suffix('.tab')):
            print(f"Removing previous Difference Log for {ceid}...")
            os.remove(pth_ceid_diffs.with_suffix('.tab'))

        print(f"Checking for changes to {ceid} Oper Grid...")
        output_path = output_dir / f'{ceid}_ops_grid.tab'
        temp_path = output_dir / f'{ceid}_ops_grid_temp.tab'

        # using a temporary copy of the grid for reformatting
        ops_grid = unpack_data(ceid, op_ent_data, df9, ceid_oper)
        ops_grid.to_csv(temp_path, sep='\t', index=False)
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
    report_config_dict = {}
    for ceid in ceid_list:
        ops_grid_key = f"{ceid}_ops_grid"
        ops_grid_val = unpack_data(ceid, op_ent_data, df9, ceid_oper)
        ops_grid_val = ops_grid_val.loc[:, ~ops_grid_val.columns.duplicated()].copy()
        process_node_df = df2[["OPERATION", "PROCESS_NODE"]].copy()
        process_node_df["OPERATION"] = process_node_df["OPERATION"].astype(str).str.strip()
        process_node_df = process_node_df.drop_duplicates(subset=["OPERATION"])
        ops_grid_val["Operation"] = ops_grid_val["Operation"].astype(str).str.strip()
        ops_grid_val = ops_grid_val.merge(process_node_df, how="left", left_on="Operation",
                                right_on="OPERATION")
        ops_grid_val.drop(["OPERATION"], axis=1, inplace=True)
        ops_grid_val["PROCESS_NODE"] = ops_grid_val["PROCESS_NODE"].fillna("")
        ops_grid_val = ops_grid_val.loc[:, ~ops_grid_val.columns.duplicated()].copy()

        report_config_dict[ceid] = {"ops_grid_key": ops_grid_key, "ops_grid": ops_grid_val}

    # Create Lists of Entities for Subset Parameter
    for k, v in report_config_dict.items():
        subset_key = f"{k}_subset"
        subset_val = report_config_dict[k]["ops_grid"]
        tool_prefix = entity_prefix_map.get(k, k).upper()
        fixed_cols = {"Operation", "Paths Open", "Recipe", "CC Used", "PROCESS_NODE"}
        subset_val = [
            x for x in subset_val.columns
            if (x not in fixed_cols) and str(x).upper().startswith(tool_prefix)
        ]
        if len(subset_val) == 0:
            subset_val = [x for x in report_config_dict[k]["ops_grid"].columns if x not in fixed_cols]

        report_config_dict[k]["subset"] = subset_val

    # saving ops grid to .csv files in output directory
    print('Saving the New Ops Grid as .tab files...')
    for k, v in report_config_dict.items():
        df = report_config_dict[k]["ops_grid"]
        pth_ceid_ops_grid = output_dir / f'{k}_ops_grid'
        df.to_csv(pth_ceid_ops_grid.with_suffix('.tab'), sep='\t', index=False)

    # Generate Report HTML Tables from Dataframes
    print("Creating Report HTML Tables...")
    for k, v in report_config_dict.items():
        oper_grid = report_config_dict[k]["ops_grid"]
        subset = report_config_dict[k]["subset"]
        table_uuid = k.lower()

        report = Styler(oper_grid,
                        table_attributes="class='table table-striped cell-borders' style='width: 100%'",
                        na_rep=" ") \
        .map(style_cells, subset=subset) \
        .hide(axis="index") \
        .to_html(table_uuid=table_uuid)

        report_config_dict[k]["report"] = report

    # Creating Difference Reports
    print("Checking for Differences in Oper Grids...")
    for k, v in report_config_dict.items():
        try:
            pth_ceid_diffs_df = output_dir / f"{k}_diffs"
            df_diffs = pd.read_csv(pth_ceid_diffs_df.with_suffix('.tab'), sep="\t")
        except (FileNotFoundError, EmptyDataError):
            df_diffs = pd.DataFrame(columns=["Operation"])

        report_config_dict[k]["diffs"] = df_diffs

    # Create Lists of Entities for Subset Parameter
    for k, v in report_config_dict.items():
        diffs = report_config_dict[k]["diffs"]
        if len(diffs) != 0:
            diff_subset = [x for x in diffs.columns if re.match(k, x)]
            diff_check = [x for x in diff_subset if "Old" in x]
        else:
            diff_subset = []
            diff_check = []

        report_config_dict[k]["diff_subset"] = diff_subset
        report_config_dict[k]["diff_check"] = diff_check

    diff_dfs = []
    for k, v in report_config_dict.items():
        diff_dfs.append(report_config_dict[k]["diffs"])

    if all(len(df) == 0 for df in diff_dfs):
        df_changes_detected = pd.DataFrame().reset_index(drop=True)
        changes_detected = False
    else:
        df_changes_detected = pd.DataFrame([{'changes_detected': 'There are Changes Detected'}]).reset_index(drop=True)
        changes_detected = True

    pth_changes_detected = output_dir / f"{module_selection}_OperGrid_Changes_Detected"
    df_changes_detected.to_csv(pth_changes_detected.with_suffix(".tab"), sep="\t")

    print("Creating Difference HTML Tables...")
    for k, v in report_config_dict.items():
        diffs = report_config_dict[k]["diffs"]
        subset = report_config_dict[k]["diff_subset"]
        check = report_config_dict[k]["diff_check"]
        table_uuid = f"{k}_diffs"
        diff_report = Styler(diffs,
                             table_attributes="class='table table-striped cell-borders' style='width: 100%'",
                             na_rep=" ") \
        .map(style_cells, subset=subset) \
        .map(style_cells_diffs, subset=check) \
        .hide(axis="index") \
        .to_html(table_uuid=table_uuid)

        report_config_dict[k]["diff_report"] = diff_report

    # Creating Lines Down Reports
    ld_list = []
    print("Checking for Lines Down Operations...")
    for k, v in report_config_dict.items():
        df = report_config_dict[k]["ops_grid"]
        df_ld = df[df["Paths Open"] == 0]["Operation"]

        report_config_dict[k]["ld"] = df_ld

        ld_list.append(df_ld)

        if len(df_ld) != 0:
            print(f"{k} - Lines Down Operation Detected")

    if all(len(df_ld) == 0 for df_ld in ld_list):
        df_lines_down = pd.DataFrame().reset_index(drop=True)
        lines_down_opers = False
    else:
        df_lines_down = pd.DataFrame([{'lines_down': 'There are Operations Lines Down'}]).reset_index(drop=True)
        lines_down_opers = True

    pth_df_lines_down = output_dir / f"{module_selection}_LinesDown_Operations"
    df_lines_down.to_csv(pth_df_lines_down.with_suffix(".tab"), sep="\t")

    print("Creating Lines Down HTML Tables...")
    for k, v in report_config_dict.items():
        df_ld = report_config_dict[k]["ld"]
        table_uuid = f"{k}_ld"

        ld_report = Styler(df_ld,
                           table_attributes="class='table table-striped cell-borders' style='width: 100%'",
                           na_rep=" ") \
        .hide(axis="index") \
        .to_html(table_uuid=table_uuid)

        report_config_dict[k]["ld_report"] = ld_report

    # Creating HTML Config Dictionaries

    output_dicts = {}
    for k, v in report_config_dict.items():
        table = report_config_dict[k]["report"]
        table_id = k.lower()
        output_dicts[k] = {
            "title": f"{k} Oper Grid",
            "heading": f"{k} Oper Grid",
            "table": table,
            "body_text": legend_table,
            "file_name": f"{k}_OperGrid",
            "table_id": table_id,
            "caption": ""
        }

    DIFFS_DICT = {
        "file_name": f"{module_selection}_OperGrid_Diffs",
        "title": "Oper Grid Differences",
        "heading": "Oper Grid Differences",
        "body_text": legend_table,
        "caption": "",
        "changes_detected": changes_detected,
        "table_ids": []
    }

    for k, v in report_config_dict.items():
        diff_table = report_config_dict[k]["diff_report"]
        DIFFS_DICT[f"{k.lower()}_table"] = diff_table

    LINES_DOWN_DICT = {
        "file_name": f"{module_selection}_Lines_Down_Operations",
        "title": "Lines Down Operations",
        "heading": "Lines Down Operations",
        "body_text": "<p>The following operations are Lines Down: </p>",
        "caption": "",
        "table_ids": [],
        "lines_down_opers": lines_down_opers
    }

    for k, v in report_config_dict.items():
        ld_table = report_config_dict[k]["ld_report"]
        LINES_DOWN_DICT[f"{k.lower()}_table"] = ld_table

    # Update DIFFS DICT if DIFF DF's are Empty
    for k, v in report_config_dict.items():
        diffs_df = report_config_dict[k]["diffs"]

        if len(diffs_df) != 0:
            DIFFS_DICT[f"{k.lower()}_table_head"] = f"{k} Oper Grid Deltas:"
            DIFFS_DICT["table_ids"].append(f"{k.lower()}_diffs")
        else:
            DIFFS_DICT[f"{k.lower()}_table"] = ""

    # Update LINES DOWN DICT if LD DF's are Empty
    for k, v in report_config_dict.items():
        ld_df = report_config_dict[k]["ld"]

        if len(ld_df) != 0:
            LINES_DOWN_DICT[f"{k.lower()}_table_head"] = f"{k} Lines Down Operations:"
            LINES_DOWN_DICT["table_ids"].append(f"{k}_ld")
        else:
            LINES_DOWN_DICT[f"{k.lower()}_table_head"] = ""
            LINES_DOWN_DICT[f"{k.lower()}_table"] = ""

    # Generating Links Dictionary for NavBar
    links = {}

    for ceid_dict in output_dicts:
        href_base = html_out_file + output_dicts[ceid_dict]["file_name"]
        # href = href_base.with_suffix(".html")

        links[f"{ceid_dict.lower()}_href"] = href_base + ".html"

    oper_grid_diffs_href_path = html_out_file + DIFFS_DICT["file_name"]
    links.update({"oper_grid_diffs_href": oper_grid_diffs_href_path + ".html"})
    lines_down_href_path = html_out_file + LINES_DOWN_DICT["file_name"]
    links.update({"oper_lines_down_href": lines_down_href_path + ".html"})


    # Writing output HTML Files with Ops Grid
    print("Writing HTML Output Files...")

    for k, v in output_dicts.items():
        write_html_output(link_dict=links, custom_css=css, searchable=True, **output_dicts[k])

    write_diffs_html_output(link_dict=links, custom_css=css, **DIFFS_DICT)
    write_lines_down_html_output(link_dict=links, custom_css=css, **LINES_DOWN_DICT)

    lines_down_email_dict = dict(LINES_DOWN_DICT)
    lines_down_email_dict["file_name"] = f"{module_selection}_Lines_Down_Operations_Email"
    write_email_html_output(link_dict=links, custom_css=css, **lines_down_email_dict)

    print("Process Completed!")


if __name__ == '__main__':
    main()
