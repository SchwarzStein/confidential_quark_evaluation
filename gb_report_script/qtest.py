import subprocess
import os
import signal
import time
from datetime import datetime
import logging
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

import argparse
from pathlib import Path
import numpy as np
import csv

SEPARATE= '====================\n'
TRY = 'Runtime:%s,Turns:%d\n'

def log(_name, path):
    ctime = datetime.now().strftime("%d-%m-%Y_%H-%M-%S");
    end_dir = path.joinpath(_name)
    if end_dir.exists() == False:
        os.makedirs(end_dir.as_posix())
    file_name = end_dir.joinpath(ctime + '.csv')
    return file_name

def parse_test_arg(args, application=None):
    cmd = ""
    port = ""
    if application == 'redis':
        port = "6379"
    elif application == 'nginx':
        port = '8080'
    else:
        port = "11211"
    match args.command:
        case 'wrk':
            dur = args.duration
            conn = args.connections
            thr = args.threads
            cmd = f'./bencht/wrk -d {dur}s -t {thr} -c {conn} http://127.0.0.1:8080/test.html'
        case 'memslap':
            ops = args.ops
            cmd = f'/home/christo/libmemcached/build/src/bin/memslap --servers=127.0.0.1:{port} -t {ops} -c 100'
        case 'memtier':
            clients = args.clients
            threads = args.threads
            ratio = args.ratio
            random = ""
            if args.random:
                random = '-R'
            cmd = f'memtier_benchmark -p {port} -s 127.0.0.1 --protocol={application} {random} '\
             f'--ratio={ratio} -c {clients} -t {threads} --hide-histogram'
        case _:
            print('Invalid test')
            return 1
    return cmd

##
## NOTE: This results should be displayed as pie-charts
def perf_from_qlog(log_name, platform, components):
    qlog_path = '/var/log/quark/quark.log'
    #Cleanup previous log
    try:
        os.remove(qlog_path)
    except OSError:
        print("Need sudo to remove previous log")
        pass
    line_grep = 'Perf:'
    grep = {
            #TODO: in Quark - {Create, CvmMemoryProtect}/1000 -> all values to us
            'creation': ['Create'],
            'start-up': ['StartUp'],
            'attestation':['Attestation'],
            'hfs-sync': ['HFiles', 'WriteBack']
            }
    env = ''
    wtime = 8
    if 'attestation' not in components:
        env = '-e "Q_AA_NO_ATTEST=y"'
        print("!!! CCQuark without Attestation !!!")
    elif 'attestation' in components or 'start-up' in components:
        env = '--network host -e Q_AA_KBS_ADDRESS=127.0.0.1:8080'
        wtime = '15'
    test = f'docker run --rm -d --cpus=30 {env} --runtime=quark ubuntu:20.04 bash -c exit'
    rounds = 10
    for i in range(rounds):
        result = subprocess.run(test, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)
        if result.stderr != '':
            print(result)
            print('QPerf: Unexpected output - possible error');
            return 1
    res = {}
    print(components)
    with open(qlog_path, 'r') as log:
        lines = log.readlines()
        for comp in components:
            data = {}
            for line in lines:
                if line_grep in line:
                    cont = line.rstrip('\n').rstrip('\x00').split(' ')[-1].split('-')
                    search = grep.get(comp)
                    for consern in search:
                        if consern in cont[0]:
                            key = cont[1]
                            if key in data:
                                data[key] += float(cont[-1])
                            else:
                                data.update({key:float(cont[-1])})
            res.update({comp:data})
    for comp in components:
        res_file = log_name.as_posix().split('.')[0] + '_' + platform.rstrip("'") + '_' + comp + '.csv'
        print(res_file)
        header = ['perf', platform + '-' + comp]
        data = res.get(comp)
        print(data)
        with open(res_file, 'a', newline='') as f:
            _writer = csv.writer(f)
            _writer.writerow(header)
            for k, v in data.items():
                row = []
                row.append(key)
                row.append((v/float(rounds))/float(1000000)) #to ms
                _writer.writerow(row)

def startup_time(log_name, runtimes=["quark"], tries=10):
    rtime = ""
    env = ''
    tmp_file = log_name.as_posix() + '.tmp'
    result = subprocess.run("docker create ubuntu:20.04", shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True)
    cid = result.stdout.split('\n')[0]
    wtime = 2
    with open(tmp_file, 'a+') as f:
        for r in runtimes:
            if r != 'native':
                rtime = "--runtime="+r
            if r == 'quark':
                env = '-e "Q_AA_NO_ATTEST=y"'
                rtime = "--runtime=quark"
            if r == 'tdx':
                env = '--network host -e "Q_AA_KBS_ADDRESS=127.0.0.1:8080"'
                rtime = "--runtime=quark"
                wtime = 15
            command = f'date +%s%N;docker run --cpus=30 --rm {rtime} {env} ubuntu:20.04 /bin/date +%s%N'
            f.write(TRY % (r, tries))
            f.write(SEPARATE)
            for i in range(tries):
                result = subprocess.run(command, shell=True, stdout=subprocess.PIPE,
                                        stderr=subprocess.STDOUT, text=True)
                vals = result.stdout.split('\n')[:-1]
                diff = (float(vals[1]) - float(vals[0])) * 10**(-9)
                f.write("%.9f\n" % diff)
                time.sleep(wtime)
    _adjust_startup_res(tmp_file, log_name)
    subprocess.run(f"docker rm -f {cid}", shell=True, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.STDOUT)

def nginx_ops(log_name, runtimes, tries=100000):
    rtime = ""
    logs = []
    env = ""
    wtime = 2
    for r in runtimes:
        if r != 'native':
            rtime = "--runtime="+r
        if r == 'quark':
            env = '-e "Q_AA_NO_ATTEST=y"'
            wtime = 3
        if r == 'tdx':
            print("!!! CCQuark without Attestation !!!")
            env = '-e "Q_AA_NO_ATTEST=y"'
            rtime = "--runtime=quark"
            wtime = 6
        cname = r+'-nginx'
        tmp_file = log_name.as_posix() + '.'+ r + '.tmp'
        command = f'docker run --cpus=30 --rm {rtime} {env} -p 80:80 --name {cname} -d nginx'
        check_ready = "ps -e|grep nginx &> /dev/null; echo $?"
        cleanup = f'docker rm -f {cname}'
        check_op = f'ab -n {tries} -c 10 http://localhost/index.html'

        with open(tmp_file, 'a', newline='') as f:
            print(f'Start test for:{cname} - file name:{tmp_file}')
            pid = os.fork()
            if pid == 0:
                subprocess.run(command, shell=True, stdout=subprocess.DEVNULL)
                return 0
            else:
                time.sleep(wtime)
                subprocess.run(check_op, shell=True, stdout=f,
                               stderr=subprocess.STDOUT, text=True)
                f.flush()
                subprocess.run(cleanup, shell=True, check=True)
                os.wait()
                logs.append(tmp_file)
            print(f'End test for:{cname} - file name:{tmp_file}')
    if len(logs) > 0:
        _adjust_nginx_res(logs)
    else:
        print("no logs from redis-ops")

def _adjust_nginx_res(logs):
    data = ['GET']
    header = ["test"]
    for f in logs:
        runtime = f.split('.')[-2]
        header.append(runtime)
        with open(f, 'r', newline='') as fd:
            content = fd.readlines()
        #    print(content)
            for line in content:
                if 'Requests ' in line:
                    rps = line.split()[-3]
                    data.append(rps)
                    break
    print("data:", data)
    log_file = logs[0].split('.')[0] + '.csv'
    with open(log_file, 'a', newline='') as f:
        _writer = csv.writer(f)
        _writer.writerow(header)
        _writer.writerow(data)

def getset_perf(lname, runtimes, image, test_cont, test):
    rtime = ""
    logs = []
    env = ""
    wtime = 3
    for r in runtimes:
        if r != 'native':
            rtime = "--runtime="+r
        if r == 'quark':
            env = '-e "Q_AA_NO_ATTEST=y"'
        if r == 'tdx':
            print("!!! CCQuark without Attestation !!!")
            env = '-e "Q_AA_NO_ATTEST=y"'
            rtime = "--runtime=quark"
            wtime = 8
        cname = r+image
        tmp_file = lname.as_posix() + '.'+ r + '.tmp'
        command = test_cont.format(rtime, cname, env)
        print(command)
        cleanup = f'docker rm -f {cname}'

        with open(tmp_file, 'a', newline='') as f:
            print(f'Start test for:{cname} - file name:{tmp_file}\ncommand:{command}\ntest:{test}')
            pid = os.fork()
            if pid == 0:
                subprocess.run(command, shell=True)
                return 0
            else:
                time.sleep(wtime)
                print(test)
                subprocess.run(test, shell=True, stdout=f,
                               stderr=subprocess.STDOUT, text=True)
                f.flush()
                subprocess.run(cleanup, shell=True, check=True)
                os.wait()
                logs.append(tmp_file)
            print(f'End test for:{cname} - file name:{tmp_file}')
    if len(logs) > 0:
        _adjust_perf_res(logs, test)
    else:
        print("no logs from get/set perf")

def _adjust_perf_res(logs, test):
    _test = test.split()
    ops = []
    clients = 0
    header = ["test"]
    memtier_bin = False
    data_pos = []
    res = {}
    if 'wrk' in _test[0]:
        ops = ["Requests", "Transfer"]
        data_pos = [1]
    elif "memslap" in _test[0]:
        ops[0] = _test[3].upper()
        clients = 100
        data_pos = [8]
    else:
        memtier_bin = True
        ops = ["Get", "Set"]
        clients = [-3]
        data_pos = [1, 8]
    for f in logs:
        runtime = f.split('.')[-2]
        header.append(runtime)
        with open(f, 'r', newline='') as fd:
            content = fd.readlines()
    #        print(content)
            for line in content:
                for el in ops:
                    if el in line:
                        output = line.split()
                        if 'Req' in el:
                            el = 'Get'
            #            print(output)
                        for i in range(len(data_pos)):
                            val = output[data_pos[i]]
                            if 'wrk' in _test[0]:
                                val = ''.join(filter(lambda x: x.isdigit() or x == '.', val))
                                if el == 'Get':
                                    val = round(float(val) / 1000, 3)
        #                    print(f'val:{val} - pos:{i} - ops:{el}' )
                            if el.upper() not in res:
                                res[el.upper()] = [val]
                            else:
                                res[el.upper()].append(val)
    print("Res:", res)
    log_file_name_base = logs[0].split('.')[0]
    print("LogFile:",log_file_name_base)
    log_files = []
    if memtier_bin:
        log_files.append(log_file_name_base + '_ops.csv')
        log_files.append(log_file_name_base + '_bd.csv')
    else:
        log_files.append(log_file_name_base + '.csv')

    for i in range(len(log_files)):
        with open(log_files[i], 'a', newline='') as f:
            _writer = csv.writer(f)
            _writer.writerow(header)
            for k, v in res.items():
                data = []
                data.append(k)
                if memtier_bin:
                    for e in range(len(v)):
                        if i == 0 and e % 2 == 0:
                            data.append(v[e])
                        elif i == 1 and e % 2 == 1:
                            data.append(v[e])
                    row = data
                else:
                    row = data + v
                _writer.writerow(row)

def redis_ops(log_name, runtimes, tries=100000):
    rtime = ""
    logs = []
    env = ""
    wtime = 3
    for r in runtimes:
        if r != 'native':
            rtime = "--runtime="+r
        if r == 'quark':
            env = '-e "Q_AA_NO_ATTEST=y"'
        if r == 'tdx':
            print("!!! CCQuark without Attestation !!!")
            env = '-e "Q_AA_NO_ATTEST=y"'
            rtime = "--runtime=quark"
            wtime = 6
        cname = r+'-redis'
        tmp_file = log_name.as_posix() + '.'+ r + '.tmp'
        command = f'docker run --rm --cpus=30 {rtime} {env} -p 6379:6379 -d --name {cname} redis'
        cleanup = f'docker rm -f {cname}'
        check_ready = "ps -e|grep redis &> /dev/null; echo $?"
        check_op = f'redis-benchmark -n {tries} -c 20 --csv'

        with open(tmp_file, 'a', newline='') as f:
            print(f'Start test for:{cname} - file name:{tmp_file}')
            pid = os.fork()
            if pid == 0:
                subprocess.run(command, shell=True)
                return 0
            else:
                time.sleep(wtime)
                subprocess.run(check_op, shell=True, stdout=f,
                               stderr=subprocess.STDOUT, text=True)
                f.flush()
                subprocess.run(cleanup, shell=True, check=True)
                os.wait()
                logs.append(tmp_file)
            print(f'End test for:{cname} - file name:{tmp_file}')
    if len(logs) > 0:
        _adjust_redis_res(logs)
    else:
        print("no logs from redis-ops")

def _adjust_redis_res(files):
    res = {}
    header = ["test"]
    for f in files:
        runtime = f.split('.')[-2]
        header.append(runtime)
        with open(f, 'r', newline='') as _csv:
            _reader = csv.reader(_csv, delimiter=',')
            for r in _reader:
                if r[0] == 'test':
                    continue
                if r[0] in res:
                    res[r[0]].append(r[1])
                else:
                    res[r[0]] = [r[1]]
    print("res:", res)
    log_file = files[0].split('.')[0] + '.csv'
    with open(log_file, 'a', newline='') as f:
        _writer = csv.writer(f)
        _writer.writerow(header)
        for k, v in res.items():
            data = []
            data.append(k)
            row = data + v
            _writer.writerow(row)

def _adjust_startup_res(src_fd, dest_file):
    data = {}
    with open(src_fd, 'r') as fd:
        content = fd.readlines()
        print(content)
        runtime = ""
        times = int((content[0].split(','))[-1].split(':')[-1].replace('\n', ''))
        for i in range(0, len(content) - times, times + 2):
            head = content[i].split(',')
            runtime = head[0].split(':')[-1]
            sum = 0
            for j in range(0, times):
                sum = sum + float(content[i+2+j].replace('\n', ''))
                data[runtime] = "%.9f" % (sum / times)
        print(data)
        with open(dest_file, 'a', newline='') as _csv:
            header = ['test']
            keys = data.keys()
            for k in keys:
                header.append(k)
            row = ['startup']
            for h in header[1:]:
                row.append(data[h])
            _writer = csv.writer(_csv)
            _writer.writerow(header)
            _writer.writerow(row)

def _ylabel(test):
    #TODO: metric
    match test:
        case 'startup':
            return 'sec'
        case 'redis':
            return 'Req/s'
        case 'nginx':
            return 'Req/s'
        case 'memcached-ops':
            return 'Req/s'
        case 'memcached-bd':
            return 'KB/s'

def _xlabel(test):
    #TODO: metric
    match test:
        case 'startup':
            return 'Runtimes'
        case 'redis':
            return 'Operations'
        case 'nginx':
            return 'Operations'
        case 'memcached-ops':
            return 'Operations'
        case 'memcached-bd':
            return 'Operations'

def _title(test):
    match test:
        case 'startup':
            return 'VM-Startup'
        case 'redis':
            return 'Redis'
        case 'nginx':
            return 'Nginx'
        case 'memcached-ops':
            return 'Memcached Request'
        case 'memcached-bd':
            return 'Memcached Data Transfer'

def build_plot(file):
    test = file.as_posix().split('/')[-2]
    # Load data from CSV
    data = np.genfromtxt(file, delimiter=',', dtype=None, names=True, encoding=None)
    # Extract data and convert categories to alphabetical letters
    value_columns = data.dtype.names[1:]  # ['native', 'runsc']
    raw_categories = np.atleast_1d(data[data.dtype.names[0]])  # ['startup']
    # Create letter-category mapping
    letter_to_category = {}
    alphabet_letters = [chr(65 + i) for i in range(26)]  # A-Z
    categories = []
    for i, cat in enumerate(raw_categories):
        letter = alphabet_letters[i] if i < 26 else f'Z_{i+1}'
        categories.append(letter)
        letter_to_category[letter] = cat

    values = np.array([np.atleast_1d(data[col]) for col in value_columns])
    # Create plot
    n_categories = len(categories)
    n_values = len(value_columns)
    fig_width = max(12, n_categories * 1.5)
    fig, ax = plt.subplots(figsize=(fig_width, 2))

    #width = 1 / max(n_values, 1)
    width = 0.8 / n_values
    x = np.arange(n_categories)
    # Plot with distinct colors
   # colors = plt.cm.tab10(np.linspace(0, 1, n_values))
   # colors = ['#CC5500', '#4ECDC4', '#45B7D1', '#F9C80E',]# '#702963']
  #  colors = ['#CC5500',  '#45B7D1', '#F9C80E',]# '#702963']
   # colors = ['#702963', '#F9C80E']
    for i in range(n_values):
        offset = width * i - width * (n_values - 1) / 2
        bars = ax.bar(x + offset, values[i], width,
                     label=value_columns[i], linewidth=0.8, color=colors[i])
    # Customize axes
    font1 = {'size':16}
    font2 = {'size':20}
    font3 = {'size':22}
    ax.set_xticks(x,)
    plt.tick_params(axis="y", labelsize=16)  # Set x-axis positions and labels
    ax.set_xticklabels(categories, fontdict=font1)
    ax.set_xlabel(_xlabel(test), fontdict=font2)
    ax.set_ylabel(_ylabel(test), fontdict=font2)
    ax.set_title(_title(test), fontdict=font3)
    ax.grid(axis='y', alpha=0.3)
    # Create comprehensive legend
    handles, labels = ax.get_legend_handles_labels()
    # Add letter-category mapping to legend
    mapping_entries = []
    for letter in categories:
        mapping_entries.append(f"{letter} = {letter_to_category[letter]}")
    # Create legend with three parts
    from matplotlib.lines import Line2D
    legend_elements = [
        *[Line2D([0], [0], color=colors[i], lw=4, label=value_columns[i])
         for i in range(n_values)],
        Line2D([0], [0], marker='', color='w', label='\n'.join(mapping_entries))
    ]
    ax.legend(handles=legend_elements,
              title='Legend:',
              bbox_to_anchor=(1, 0.92),
              loc='upper left')
    plt.tight_layout(rect=[0, 0, 0.8, 1])
    plt.show()

def plot_mmc():
    # Intel
    tee = "tdx"
    #Memcached
   # set_runc = [33713.984, 77224.303, 119399.189]
   # get_runc = [336769.356, 192790.74, 149034.239]
   # set_runsc = [7027.756, 21597.985, 33878.117]
   # get_runsc = [70200.326, 53919.444, 42286.714]
   # set_quark = [9099.149, 29687.059, 46192.115]
   # get_quark = [90891.501, 74113.844, 57657.064]
    set_qemcc = [9434.777, 29533.646, 45989.712]
    get_qemcc = [94244.093, 73730.850, 57404.424]
    set_tee = [9391.665, 29583.425, 45844.75]
    get_tee = [93813.454, 73855.125, 57223.482]
   #Nignx
    ####
    ### Plot me
    ####
   # get_runc = [14842.975, 15467.392, 16177.27, 16700.588]
   # get_runsc = [3442.968, 5138.291, 5717.167, 6049.983]
   # get_quark = [5974.89, 6300.371, 6236.85, 6419.095]
   # get_qemcc = [5866.413, 6081.976, 6170.58, 6068.822]
   # get_tee = [5492.329, 5706.164, 5782.379, 5765.049]

    # AMD
   # tee = "sev/snp"
   # Memcached
   # set_runc = [21264.849, 66292.347, 103220.749]
   # get_runc = [212414.807, 165499.079, 128840.289]
   # set_runsc = [4990.513, 15661.453, 23869.959]
   # get_runsc = [49850.297, 39098.872, 29794.517]
   # set_quark = [7229.14, 22283.68, 35117.321]
   # get_quark = [72211.962, 55631.284, 43833.491]
   # set_qemcc = [7192.822, 23542.389, 35533.07]
   # get_qemcc = [71849.176, 58773.656, 58084.286]
   # #set_tee = [7109.602, 17614.234, 35188.592]
   # set_tee = [7109.602, 20440.246, 35188.592]
   # #get_tee = [71017.898, 43973.996, 43922.451]
  #  get_tee = [71017.898, 51028.641, 43922.451]
   #Nignx
  #  get_runc = [13791.191, 13704.368, 13643.241, 13422.283]
  #  get_runsc = [8881.341, 10986.372, 10989.43, 11063.282]
  #  get_quark = [8075.541, 8367.255, 8771.053, 9167.075]
  #  get_qemcc = [8051.914, 8383.786, 8864.321, 9195.709]
  #  get_tee = [7803.496, 8167.282, 8585.827, 8989.109]

    #x = np.array([0,1,2])
   # x = np.array([0,1,2,4])
    x_positions = [0, 1, 2]
   # x_positions = [0,1,2,4]
    x_labels = ["1:10", "4:10", "8:10"]
   # x_labels = ["10", "40", "80", "120"]
    font3 = {'size':15}
    plt.figure(figsize=(10, 6))
    # Plot all datasets with specified styles
    # f-series (red)
   # plt.plot(x_positions, set_runc, '--r', marker='o', markersize=8, label='SET#runc', linewidth=2)
   # plt.plot(x_positions, get_runc, '-r', marker='x', markersize=8, label='GET#runc', linewidth=2)
   ###### # b-series (green)
   # plt.plot(x_positions, set_runsc, '--g', marker='o', markersize=8, label='SET#runsc', linewidth=2)
   # plt.plot(x_positions, get_runsc, '-g', marker='x', markersize=8, label='GET#runsc', linewidth=2)
   ###### # g-series (blue)
   # plt.plot(x_positions, set_quark, '--b', marker='o', markersize=8, label='SET#quark', linewidth=2)
   # plt.plot(x_positions, get_quark, '-b', marker='x', markersize=8, label='GET#quark', linewidth=2)
    plt.plot(x_positions, set_qemcc, '--b', marker='o', markersize=8, label='SET#quark-emcc', linewidth=2)
    plt.plot(x_positions, get_qemcc, '-b', marker='x', markersize=8, label='GET#quark-emcc', linewidth=2)
    # m-series (yellow)
    plt.plot(x_positions, set_tee, '--y', marker='o', markersize=8, label='SET#'+tee, linewidth=2)
    plt.plot(x_positions, get_tee, '-y', marker='x', markersize=8, label='GET#'+tee, linewidth=2)
    # Configure plot appearance
    font2 = {'size':18}

    plt.xticks(x_positions, x_labels, fontdict=font3)  # Set x-axis positions and labels
    plt.tick_params(axis="y", labelsize=16)  # Set x-axis positions and labels
   # plt.xlabel('SET:GET(1.000.000 Request)', fontdict=font2)
    plt.xlabel('Request Ratio', fontdict=font2)
    plt.ylabel('Req/sek', fontdict=font2)
    plt.title('Memcached', fontdict=font2)
   # plt.title('Nginx', fontdict=font2)
   # plt.xlabel('Clients', fontdict=font2)
    plt.grid(True, linestyle='--', alpha=0.7)
    # Combine legends and avoid duplicates
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))  # Remove duplicate labels
    plt.legend(by_label.values(), by_label.keys(), ncol=2,fontsize=14)
    plt.tight_layout()
    plt.show()

def startup_bar():
   # percentages = [15.26, 9.31, 17.93, 5.128, 52.372]
   # categories = ["VMM#MemInitialize", "VMM#EncryptMemory", "VM#BspInitialize", "VM#RemoteAttestation", "Other"]
   # colors = ['#CC5500', '#4ECDC4', '#45B7D1', '#F9C80E', '#702963']
    percentages = [39.5, 18.5, 42.0]
    categories = ["VMM#EncryptMemory", "VM#RemoteAttestation-GetToken", "Other"]
    colors = ['#4ECDC4', '#F9C80E', '#702963']
# C#reate figure with appropriate size for academic paper
   # plt.rcParams.update({'font.size': 15, 'font.family': 'serif'})
   # fig, ax = plt.subplots(figsize=(13, 1.6))  # Wider and thinner bar
   # 
   # # Initialize left position for stacking
   # bottom = 0
   # 
   # # Create each segment of the bar
   # for percent, category, color in zip(percentages, categories, colors):
   #     ax.bar(0, percent, bottom=bottom, color=color, label=category, 
   #             width=0.6, edgecolor='white', linewidth=0.8)
   #     bottom += percent
   # 
   # # Format x-axis as percentage
   # ax.set_xlim(0, 100)
   # ax.xaxis.set_major_formatter(mtick.PercentFormatter())
   # 
   # # Remove y-axis labels and ticks
   # ax.set_yticks([])
   # ax.spines['top'].set_visible(False)
   # ax.spines['right'].set_visible(False)
   # ax.spines['left'].set_visible(False)
   # 
   # # Add title and labels with larger font
   # plt.title('Distribution of Components', pad=20, fontsize=18, fontweight='bold')
   # plt.xlabel('Percentage', fontsize=16, fontweight='bold')
   # 
   # # Add legend with larger font
   ## legend = plt.legend(bbox_to_anchor=(0.9, 0.3), loc='center left', 
   ##                     frameon=False, fontsize=16)
   ## plt.setp(legend.get_texts(), fontweight='bold')
   # 
   # # Add value labels on each segment with larger font
   # left = 0
   # for percent in percentages:
   #     if percent > 5:  # Only label segments large enough to contain text
   #         plt.text(left + percent/2, 0, f'{percent:.1f}%', 
   #                  ha='center', va='center', fontweight='bold', 
   #                  color='white', fontsize=14)
   #     left += percent
   # 
   # # Adjust layout to prevent cutting off elements
   # plt.tight_layout()
   # 
   # # Save as high-quality PNG for academic paper
   # plt.savefig('stacked_bar_chart.png', dpi=300, bbox_inches='tight')
   # plt.show()
    # Create figure with appropriate size for academic paper
    plt.rcParams.update({
        'font.size': 16,
        'font.family': 'serif',
        'axes.titlesize': 18,
        'axes.labelsize': 15,
        'legend.fontsize': 15
    })
    
    fig, ax = plt.subplots(figsize=(8, 3))  # Adjusted for vertical bar
    
    # Initialize bottom position for stacking
    bottom = 0
    
    # Create each segment of the bar
    for percent, category, color in zip(percentages, categories, colors):
        ax.bar(0, percent, bottom=bottom, color=color, label=category, 
               width=0.6, edgecolor='white', linewidth=0.8)
        bottom += percent
    
    # Format y-axis as percentage
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    
    # Remove x-axis labels and ticks
    ax.set_xticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    
    # Add title and labels with larger font
    plt.title('Sev/Snp-VM Launch Sections', pad=20,)
    plt.ylabel('Time (%)',)
    
    # Add legend with larger font
    legend = plt.legend(bbox_to_anchor=(1.05, 0.5), loc='center left', 
                        frameon=False)
    plt.setp(legend.get_texts())
    
    # Add value labels on each segment with larger font
    bottom = 0
    for percent in percentages:
        if percent > 5:  # Only label segments large enough to contain text
            plt.text(0, bottom + percent/2, f'{percent:.1f}%', 
                     ha='center', va='center', fontweight='bold', 
                     color='white', fontsize=15)
        bottom += percent
    
    # Adjust layout to prevent cutting off elements
    plt.tight_layout()
    
    # Save as high-quality PDF for academic paper
    plt.savefig('vertical_stacked_bar_chart.pdf', format='pdf', bbox_inches='tight', dpi=300)
    plt.show()

def startup_pie():
    #TDX
    tee = "TDX"
    y = np.array([15.26, 9.31, 17.93, 5.128,52.372])
    mylabels = ["VMM#MemInitialize", "VMM#EncryptMemory", "VM#BspInitialize", "VM#RemoteAttestation", "Other"]
    #SNP
   # tee = "SnpSev"
   # y = np.array([39.5, 18.5, 42.0])
   # mylabels = ["VMM#EncryptMemory", "VM#RemoteAttestation-GetToken", "Other"]

    plt.legend(title = "Startup-"+tee+"(%Time)")
    plt.pie(y, labels = mylabels, startangle = 90, counterclock=False)
    plt.show()


def main():
    argpars = argparse.ArgumentParser(add_help=False)
    argpars.add_argument('--type', help='Performance measurement or plot collected data',
                         choices=['startup', 'redis-ops', 'nginx-ops', 'memcached-ops',
                                  'quark-rt', 'plot'],
                         default='startup')
    argpars.add_argument('--runtime', help='Select the runtime for tests (not applyed for "plot")',
                         choices=['all', 'native', 'runsc', 'quark', 'tdx'], nargs='+',
                         default=['all'])
    argpars.add_argument('--path', help='All except "plot":Directory to save measurement \
        \nreport Only for "plot":Create a plot from the passed file', type=Path)
    argpars.add_argument('--for', help='(Temporay command) Select the test type to plot',
                         choices=['startup', 'redis', 'nginx'], nargs=1, default='startup')

    subparsers = argpars.add_subparsers(dest='command', metavar={'memtier', 'memslap', 'wrk', 'qperf'})
    bench_qperf = subparsers.add_parser('qperf', add_help=False)
    bench_qperf.add_argument('--platform', choices=['native', 'realm', 'tdx', 'sevsnp'], default='native')
    bench_qperf.add_argument('--component', choices=['attestation', 'creation', 'start-up', 'hfs-sync'],
                             default=['creation'], nargs='+')
    bench_wrk = subparsers.add_parser('wrk', add_help=False)
    bench_wrk.add_argument('--duration', help='Duration of test', type=int, default='60')
    bench_wrk.add_argument('--connections', help='Number of connections (>= threads)', type=int, default='4')
    bench_wrk.add_argument('--threads', help='Number of threads to spawn', type=int, default='4')

    bench_memtier = subparsers.add_parser('memtier', add_help=False)
    bench_memtier.add_argument('--random', action='store_false', help='Randomized data access')
    bench_memtier.add_argument('--ratio', help='specify ops ratio SET:GET', default='1:10')
    bench_memtier.add_argument('--clients', help='specify number of clients', default='100')
    bench_memtier.add_argument('--threads', help='specify number of threads', default='8')

    bench_memslap = subparsers.add_parser('memslap', add_help=False)
    bench_memslap.add_argument('--ops', choices =['get', 'set'], default='get',
                         help='Benchmark (Redis, Memcached) for ops:"GET, SET" for 10000 keys x 100 threads.')

    args = argpars.parse_args()
    print(args)
    cmd_type = args.type
    log_path = args.path
    if cmd_type == 'plot':
        build_plot(log_path)
    #    print("##### Ploting Memcached #####")
    #   print("##### Ploting Nginx #####")
    #    plot_mmc()
       # print("### Plot Pie ###")
       # startup_pie()
       # startup_bar()
    else:
        lname = log(cmd_type, log_path)
        runtimes = []
        match args.runtime[0]:
            case 'all':
                print("!!! CC-Quark NOT included !!!")
                runtimes = ['native', 'runsc', 'quark']
            case _:
                runtimes = args.runtime
        try:
            match cmd_type:
                case 'startup':
                    startup_time(lname, runtimes)
               # case 'qperf':
               #     perf_from_qlog(lname, runtimes)
                case 'redis-ops':
                    if args.command == 'memtier':
                        test = parse_test_arg(args, 'redis')
                        test_cnt = 'docker run --rm {0} --cpus=30 {2} -p 6379:6379 --name {1} -d redis'
                        print(test_cnt)
                        getset_perf(lname, runtimes, '-redis', test_cnt, test)
                    else:
                        redis_ops(lname, runtimes)
                case 'nginx-ops':
                    if args.command == 'wrk':
                        test = parse_test_arg(args, 'nginx')
                        test_cnt = 'docker run --rm {0} --cpus=30 {2} -d -p 8080:80 --name {1} -v $(realpath .)'\
                        '/becht/http-test-files:/usr/share/nginx/html nginx'
                        getset_perf(lname, runtimes, '-nginx', test_cnt, test)
                    else:
                        nginx_ops(lname, runtimes)
                case 'memcached-ops':
                    test = parse_test_arg(args, 'memcache_text')
                    test_cnt = 'docker run --rm {0} --cpus=30 {2} -p 11211:11211 --name {1} -d memcached'
                    getset_perf(lname, runtimes, '-memcached', test_cnt, test)
                case 'quark-rt':
                     perf_from_qlog(lname, args.platform, args.component)
                case _:
                     print(f'Error: command \'cmd_type\' not implemented')
                     return 1
        except Exception as ex:
            logging.exception(ex)
            os.remove(lname)
            return

if __name__ == "__main__":
    main()
