import fnmatch
import json
import os
import platform
import shutil
import signal
import time

import psutil
import yaml
from yaml.loader import SafeLoader

# To run a zenoh-flow configuration other than the getting started example enter here the yaml file path.
data_flow_path = [""]
# or alternatively here you can enter the name of the yaml configuration file. In this case the file name must be unique.
# i.e. period-miss-detector.yaml
data_flow_file = ""


class ZF_conf:
    def __init__(self):
        self.zenohd_path = None
        self.zf_plugin_path = None
        self.zf_router_path = None
        self.zenohd_process = None
        self.zfctl_path = None
        self.zfctl_json_path = None
        self.zf_deamon_yaml = None
        self.zenoh_flow_daemon = None
        self.uuid_runtimes = None
        self.libzenoh_plugin = None


zf_conf = ZF_conf()

zf_command = {
    "zenohd_cmd": None,
    "runtimes_cmd": None,
    "dataflow_yaml_cmd": None,
    "instances_cmd": None,
}
instance = {
    "uuid_instances": None,
    "flow": None,
    "operators": None,
    "sinks": None,
    "sources": None,
    "connectors": None,
    "links": None,
}


def find_dir(name, path):
    for root, dirs, files in os.walk(path):
        if name in dirs:
            return os.path.join(root, name)


def find(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


pid_zenohd = 0
json_flag = False
zenoh_release_flag = False
zenohflow_release_flag = False

print("[info] Looking for paths...")
manual_tests_path = os.getcwd()
home_path = os.path.expanduser("~")
zenohd_path = os.path.abspath(os.path.join(manual_tests_path, os.pardir))
zenoh_flow_path = os.path.abspath(os.path.join(manual_tests_path, os.pardir))
zf_conf.zenohd_path = find("zenohd", home_path)
print(f"Path of zenohd: {zf_conf.zenohd_path[0]}")

par_dir = os.path.abspath(os.path.join(zf_conf.zenohd_path[0], os.pardir))
dir, _ = os.path.split(zf_conf.zenohd_path[0])
_, base = os.path.split(dir)
three_up = os.path.abspath(os.path.join(zf_conf.zenohd_path[0], "../../.."))

if base == "release":
    print(f"[info] set Zenoh artifact directory: {base}")
    zenoh_release_flag = True

if os.path.exists(os.path.join(zenoh_flow_path, "/target/release")):
    print(f"[info] set Zenoh-Flow artifact directory: {base}")
    zenohflow_release_flag = True

zenoh_path = find_dir("zenoh", three_up)
print(f"Path of zenoh: {zenoh_path}")

if data_flow_file == "" and data_flow_path == "":
    data_flow_path = find("getting-started.yaml", zenoh_flow_path)
elif data_flow_file != "" and data_flow_path != "":
    data_flow_path = find(data_flow_file, zenoh_flow_path)

print(f"Path of getting-started example: {data_flow_path[0]}")

print("[info] Looking for json file...")
if os.path.exists(os.path.join(manual_tests_path, "test.json")):
    test_json_path = "test.json"
    with open(
        os.path.join(manual_tests_path, "test.json"), encoding="utf-8"
    ) as json_file:
        print("[info] Reading json file...")
        zf_command = json.load(json_file)

if any(v is None for v in zf_command.values()):
    os.chdir(zenoh_path)
    if zenoh_release_flag is True:
        build_zenoh = "cargo build --release --features shared-memory"
    elif zenoh_release_flag is False:
        build_zenoh = "cargo build --features shared-memory"
    os.system(build_zenoh)

    print("[info] Compiling Zenoh-Flow Examples")
    os.chdir(zenoh_flow_path)
    if zenoh_release_flag is True:
        build_zenohflow_examples = "cargo build --release --examples "
    elif zenoh_release_flag is False:
        build_zenohflow_examples = "cargo build --examples"
    os.system(build_zenohflow_examples)
    os.chdir(manual_tests_path)
    zenoh_zf_plugin_path = find("zenoh-zf-plugin.json", zenoh_flow_path)
    print(f"Path of plugin library: {zenoh_zf_plugin_path[0]}")

    lib_name = ""
    if platform.system() == "Windows":
        lib_name = "libzenoh_plugin_zenoh_flow.dll"
    elif platform.system() == "Linux":
        lib_name = "libzenoh_plugin_zenoh_flow.so"
    elif platform.system() == "Darwin":
        lib_name = "libzenoh_plugin_zenoh_flow.dylib"

    libzenoh_plugin_path = find(lib_name, zenoh_flow_path)
    zf_conf.libzenoh_plugin = libzenoh_plugin_path[0]
    print(f"Path of plugin Zenoh-Flow library: {zf_conf.libzenoh_plugin}")
    libdir, libbase = os.path.split(libzenoh_plugin_path[0])

    zfctl_path = find("zfctl", zenoh_flow_path)
    zf_conf.zfctl_path = zfctl_path[0]
    print(f"Path of zfctl: {zf_conf.zfctl_path}")

    print("[info] Zenoh-Flow as Zenoh plugin")
    if os.path.exists(os.path.join(manual_tests_path, "zenoh-zf-plugin.json")) is False:
        shutil.copy(zenoh_zf_plugin_path[0], manual_tests_path)
    add_lib_folder = ""

    zf_conf.zf_plugin_path = os.path.join(manual_tests_path, "zenoh-zf-plugin.json")
    with open(zenoh_zf_plugin_path[0]) as json_file:
        json_string = json_file.read()
        if json_string.find(libdir) == -1:
            start_row = json_string.find('"plugins_search_dirs":[')
            index = (start_row - 1) + '"plugins_search_dirs": ['.__len__()
            add_lib_folder = (
                json_string[:index] + '"' + libdir + '",' + json_string[index:]
            )

    if add_lib_folder != "":
        with open(zf_conf.zf_plugin_path, "w", encoding="utf8") as json_file:
            json_file.write(add_lib_folder)

    print("[info] Commands:")
    zf_command["zenohd_cmd"] = zf_conf.zenohd_path[0] + " -c " + zf_conf.zf_plugin_path
    print(f'Lauch Zenoh with Zenoh-Flow plugin: \n {zf_command["zenohd_cmd"]}')
    zf_command["runtimes_cmd"] = zf_conf.zfctl_path + " list runtimes"
    print(f'show the list of runtimes: \n {zf_command["runtimes_cmd"]}')
    zf_command["dataflow_yaml_cmd"] = (
        zf_conf.zfctl_path + " launch " + data_flow_path[0]
    )
    print(f'Lauch Zenoh-Flow configuration: \n {zf_command["dataflow_yaml_cmd"]}')
    zf_command["instances_cmd"] = zf_conf.zfctl_path + " list instances"
    print(f'show list of Zenoh-Flow instances: \n {zf_command["instances_cmd"]}')

print("[info] Looking for Zenohd process...")
process_name = "zenohd"
pid = None
for process in psutil.process_iter():
    if process_name in process.name():
        pid = process.pid
        print(f"[info] kill process: {pid}")
        os.kill(pid, signal.SIGKILL)
        break

print(f'[info] Launching Zenod process: {zf_command["zenohd_cmd"]}')
launch_zenohd = os.popen(zf_command["zenohd_cmd"])
print("Waiting for zenohd...")
time.sleep(5)
pid = ""
for process in psutil.process_iter():
    if process_name in process.name():
        pid = process.pid
        break

print(f"[info] Test {process_name}  process pid {pid}")
zf_conf.zenohd_process = pid
if zf_conf.zenohd_process is not None:
    print(f'[info] Launching list runtimes command: {zf_command["runtimes_cmd"]}')
    launch_runtimes = os.popen(zf_command["runtimes_cmd"])
    runtimes_string = launch_runtimes.read().split()
    for i in range(runtimes_string.__len__()):
        if runtimes_string[i].__len__() == 32 and runtimes_string[i - 2][0] == "+":
            print("[info] test runtime: SUCCESS.")
            print(f"[info] UUID runtime: {runtimes_string[i]}")
            zf_conf.uuid_runtimes = runtimes_string[i]
    if zf_conf.uuid_runtimes is None:
        print("[info] test runtime: FAILED.")

    print(f'[info] Launching Zenoh-Flow example: {zf_command["dataflow_yaml_cmd"]}')

    launch_zf_yaml = os.popen(zf_command["dataflow_yaml_cmd"])

    zf_example_string = launch_zf_yaml.read()
    print(f"[info] zf_example_string: {zf_example_string}")
    if zf_example_string.__len__() == 0:
        print("[Error] Zenoh-Flow example: FAILED.")
    else:
        zf_conf.uuid_runtimes = zf_example_string
        print(f"[info] Zenoh-Flow example UUID: {zf_conf.uuid_runtimes}")

    print(f'[info] Launching list instances: {zf_command["instances_cmd"]}')
    launch_instances = os.popen(zf_command["instances_cmd"])
    count = 0
    instances_string = launch_instances.read().split()
    for i in range(instances_string.__len__()):
        if instances_string[i][0] == "+":
            count = count + 1
    if count <= 2:
        print("[Error] test data flow: FAILED.")
        exit()
    else:
        print("[info] test data flow instance: SUCCESS.")
        instance["uuid_instances"] = instances_string[23]
        instance["flow"] = instances_string[25]
        instance["operators"] = instances_string[27]
        instance["sinks"] = instances_string[29]
        instance["sources"] = instances_string[31]
        instance["connectors"] = instances_string[33]
        instance["links"] = instances_string[35]
else:
    print("[Error] test zenohd process: FAILED.")


with open(data_flow_path[0], "r") as f:
    try:
        data = yaml.load(f, Loader=SafeLoader)
    except yaml.YAMLError as e:
        print(f"[Error] {e}")

    if str(tuple(data["sources"]).__len__()) == instance["sources"]:
        print(
            f'[info] test active Source nodes: SUCCESS, the active Source nodes [{str(tuple(data["sources"]).__len__())}] are equal to declared Source nodes [{instance["sources"]}]'
        )
    if str(tuple(data["sinks"]).__len__()) == instance["sinks"]:
        print(
            f'[info] test active Sink nodes: SUCCESS, the active Sink nodes [{str(tuple(data["sinks"]).__len__())}] are equal to those declared Sinks nodes [{instance["sinks"]}]'
        )
    if str(tuple(data["operators"]).__len__()) == instance["operators"]:
        print(
            f'[info] test active Operator nodes: SUCCESS, the active Operator nodes [{str(tuple(data["operators"]).__len__())}] are equal declared Operator nodes [{instance["operators"]}]'
        )
    if (
        str(tuple(data["sources"]).__len__()) != instance["sources"]
        or str(tuple(data["sinks"]).__len__()) != instance["sinks"]
        or str(tuple(data["operators"]).__len__()) != instance["operators"]
    ):
        print("[Error] Test Zenoh-Flow configuration nodesSome nodes:  FAILED.")

if json_flag is False:
    f = open(os.path.join(manual_tests_path, "test.json"), "w")
    json.dump(zf_command, f)
    f.close()

    print("\n[info] Commands:")
    print(zf_command["zenohd_cmd"])
    print(zf_command["runtimes_cmd"])
    print(zf_command["dataflow_yaml_cmd"])
    print(zf_command["instances_cmd"])
