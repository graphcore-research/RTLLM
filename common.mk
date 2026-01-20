.PHONY: vcs sim clean

SRC_PATH ?= .

vcs:
	iverilog -g2012 -o simv $(SRC_PATH)/$(TEST_DESIGN).v testbench.v 2>&1 | tee compile.log

sim:
	vvp simv 2>&1 | tee run.log

clean:
	rm -f simv *.log *.vcd output.txt