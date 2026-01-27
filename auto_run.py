import os
import signal
import subprocess
from pathlib import Path
import tqdm
from scipy.special import comb


def exec_shell(cmd_str, timeout=8, cwd=None):
    try:
        proc = subprocess.Popen(
            cmd_str,
            shell=True,
            cwd=cwd,
            start_new_session=True,  # Creates new process group
        )
        proc.wait(timeout=timeout)
        return 1
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGKILL)  # Kill entire process group
        proc.wait()  # Reap zombie
        return 0


def cal_atk(dic_list, n, k):
    #syntax 
    sum_list = []
    for design in dic_list.keys():
        c = dic_list[design]['syntax_success']
        sum_list.append(1 - comb(n - c, k) / comb(n, k))
    syntax_passk = sum(sum_list) / len(sum_list) if sum_list else 0
    
    #func
    sum_list = []
    for design in dic_list.keys():
        c = dic_list[design]['func_success']
        sum_list.append(1 - comb(n - c, k) / comb(n, k))
    func_passk = sum(sum_list) / len(sum_list) if sum_list else 0
    print(f'syntax pass@{k}: {syntax_passk},   func pass@{k}: {func_passk}')


design_name = ['accu', 'adder_8bit', 'adder_16bit', 'adder_32bit', 'adder_pipe_64bit', 'asyn_fifo', 'calendar', 'counter_12', 'edge_detect',
               'freq_div', 'fsm', 'JC_counter', 'multi_16bit', 'multi_booth_8bit', 'multi_pipe_4bit', 'multi_pipe_8bit', 'parallel2serial' , 'pe' , 'pulse_detect',
               'radix2_div', 'RAM', 'right_shifter',  'serial2parallel', 'signal_generator','synchronizer', 'alu', 'div_16bit', 'traffic_light', 'width_8to16']

base_path = Path("_chatgpt4").resolve()

# Count test files to set progress bar total
num_test_files = 0
file_id = 1
while (base_path / f"t{file_id}").exists():
    num_test_files += 1
    file_id += 1
progress_bar = tqdm.tqdm(total=len(design_name) * num_test_files)
result_dic = {key: {} for key in design_name}
for item in design_name:
    result_dic[item]['syntax_success'] = 0
    result_dic[item]['func_success'] = 0


def test_one_file(testfile, result_dic):
    src_path = base_path / testfile
    for design in design_name:
        design_dir = Path(design).resolve()
        if (design_dir / "makefile").exists():
            subprocess.run(f"make vcs SRC_PATH={src_path}", shell=True, cwd=design_dir)

            if (design_dir / "simv").exists():
                result_dic[design]['syntax_success'] += 1
                to_flag = exec_shell("make sim > output.txt", cwd=design_dir)
                if to_flag == 1:
                    output = (design_dir / "output.txt").read_text()
                    if "Pass" in output or "pass" in output:
                        result_dic[design]['func_success'] += 1

            subprocess.run("make clean", shell=True, cwd=design_dir)
            progress_bar.update(1)

    return result_dic

file_id = 1
n = 0
while (base_path / f"t{file_id}").exists():
    # if file_id == 5:
    #     break
    result_dic = test_one_file(f"t{file_id}", result_dic)
    n += 1
    file_id += 1
print(result_dic)
cal_atk(result_dic, n, 1)
total_syntax_success = 0
total_func_success = 0
for item in design_name:
    if result_dic[item]['syntax_success'] != 0:
        total_syntax_success += 1
    if result_dic[item]['func_success'] != 0:
        total_func_success += 1
print(f'total_syntax_success: {total_syntax_success}/{len(design_name)}')
print(f'total_func_success: {total_func_success}/{len(design_name)}')
# print(f"Syntax Success: {syntax_success}/{len(design_name)}")
# print(f"Functional Success: {func_success}/{len(design_name)}")
