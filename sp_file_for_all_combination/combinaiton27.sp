.TITLE 3NAND_2_NP_errorall

.OPTION POST=2 POST_VERSION=2001  $ Generate .tr0 file
.OPTION MTTHRESH=10               $ Multi-core operation if >10 transitor
.OPTION PROBE                    $ Nanosim requires this line
.OPTION INGOLD                  $ 指定输出结果的显示格式
.PROBE TRAN V(*) I(i_n1) I(i_n2) I(i_n3) I(i_n4) I(i_n5) I(i_n6) I(i_n7) I(i_n8) I(i_n9) I(i_p1) I(i_p2) I(i_p3) I(i_p4) I(i_p5) I(i_p6) I(i_p7) I(i_p8) I(i_p9) I(i_cd)       $ Nanosim requires to specify output node


.TEMP = 27                    
.param vdd = 1.8

.TRAN 1p simtime
.param injection_timing_n1 = 100n   ***N_and_3
.param current_height = -4000e-6   * 4000e-6   ***100e-6 = 0.1mA  

*** 输出error pulse的注入时间
.MEASURE TRAN error_pulse_injection_timing PARAM=injection_timing_n1

*** 测量信号 n_and_3, n_and_4, cd_3, cd_4 波形宽度 pulse_width (OK)
.MEASURE TRAN n_and_3_pulse_width TRIG V(n_and_3) VAL=0.1 RISE=5 TARG V(n_and_3) VAL=0.1 FALL=5
.MEASURE TRAN n_and_4_pulse_width TRIG V(n_and_4) VAL=0.1 RISE=5 TARG V(n_and_4) VAL=0.1 FALL=5
.MEASURE TRAN cd_3_pulse_width TRIG V(cd_3) VAL=0.1 FALL=5 TARG V(cd_3) VAL=0.1 RISE=5 
.MEASURE TRAN cd_4_pulse_width TRIG V(cd_4) VAL=0.1 RISE=5 TARG V(cd_4) VAL=0.1 FALL=5


*** 测量周期 n_and_3, n_and_4, cd_3, cd_4 的周期 period (OK)
*** 用第二次到达VDD的timing 减去 第一次到达VDD的timing 的时间差作为周期
.MEASURE TRAN n_and_3_timing1 WHEN V(n_and_3)='vdd/2' RISE=3
.MEASURE TRAN n_and_3_timing2 WHEN V(n_and_3)='vdd/2' RISE=4
.MEASURE TRAN n_and_3_period PARAM='n_and_3_timing2-n_and_3_timing1'

.MEASURE TRAN n_and_4_timing1 WHEN V(n_and_4)='vdd/2' RISE=3
.MEASURE TRAN n_and_4_timing2 WHEN V(n_and_4)='vdd/2' RISE=4
.MEASURE TRAN n_and_4_period PARAM='n_and_4_timing2-n_and_4_timing1'

.MEASURE TRAN cd_3_timing1 WHEN V(cd_3)='vdd/2' RISE=3
.MEASURE TRAN cd_3_timing2 WHEN V(cd_3)='vdd/2' RISE=4
.MEASURE TRAN cd_3_period PARAM='cd_3_timing2-cd_3_timing1'

.MEASURE TRAN cd_4_timing1 WHEN V(cd_4)='vdd/2' RISE=3
.MEASURE TRAN cd_4_timing2 WHEN V(cd_4)='vdd/2' RISE=4
.MEASURE TRAN cd_4_period PARAM='cd_4_timing2-cd_4_timing1'


*** 判断deadlock
*** 测量注入pulse_width的timing的前面最近的一个上升点
.MEASURE TRAN n_and_3_rise_timing_before_pulse WHEN V(n_and_3)=0.1 RISE=LAST TO=injection_timing_n1
.MEASURE TRAN n_and_4_rise_timing_before_pulse WHEN V(n_and_4)=0.1 RISE=LAST TO=injection_timing_n1
.MEASURE TRAN cd_4_rise_timing_before_pulse WHEN V(cd_4)=0.1 CROSS=LAST TO=injection_timing_n1


*** 注入 error pulse 之后 第一, 二， 三次电压的 rise 和 fall 的 timing
*** 若只是第一次有确切的时间， 第二次和第三次均为 failed(null)则说明出现了 deadlock 错误
.MEASURE TRAN n_and_3_rise_timing_1 WHEN V(n_and_3)=0.1 RISE=1 FROM=injection_timing_n1
.MEASURE TRAN n_and_3_fall_timing_1 WHEN V(n_and_3)=0.1 FALL=1 FROM=injection_timing_n1
.MEASURE TRAN n_and_3_rise_timing_2 WHEN V(n_and_3)=0.1 RISE=2 FROM=injection_timing_n1
.MEASURE TRAN n_and_3_fall_timing_2 WHEN V(n_and_3)=0.1 FALL=2 FROM=injection_timing_n1
.MEASURE TRAN n_and_3_rise_timing_3 WHEN V(n_and_3)=0.1 RISE=3 FROM=injection_timing_n1
.MEASURE TRAN n_and_3_fall_timing_3 WHEN V(n_and_3)=0.1 FALL=3 FROM=injection_timing_n1
.MEASURE TRAN n_and_3_fall_timing_4 WHEN V(n_and_3)=0.1 FALL=4 FROM=injection_timing_n1


.MEASURE TRAN cd_4_rise_timing_1 WHEN V(cd_4)=0.05 RISE=1 FROM=injection_timing_n1
.MEASURE TRAN cd_4_fall_timing_1 WHEN V(cd_4)=0.05 FALL=1 FROM=injection_timing_n1
.MEASURE TRAN cd_4_rise_timing_2 WHEN V(cd_4)=0.05 RISE=2 FROM=injection_timing_n1
.MEASURE TRAN cd_4_fall_timing_2 WHEN V(cd_4)=0.05 FALL=2 FROM=injection_timing_n1


*** 判断正常波形
*** 在injection timing之后两个周期内的pulse_width与之前的测量结果n_and_3_pulse_width大致相同 且最大电压约为VDD
.MEASURE TRAN n_and_3_pulse_width_after_pulse_in_period1_1 PARAM='n_and_3_fall_timing_1 - n_and_3_rise_timing_1'
.MEASURE TRAN n_and_3_pulse_width_after_pulse_in_period1_2 PARAM='n_and_3_fall_timing_2 - n_and_3_rise_timing_1'

.MEASURE TRAN n_and_3_pulse_width_after_pulse_in_period2_1 PARAM='n_and_3_fall_timing_2 - n_and_3_rise_timing_2'
.MEASURE TRAN n_and_3_pulse_width_after_pulse_in_period2_2 PARAM='n_and_3_fall_timing_3 - n_and_3_rise_timing_2'

.MEASURE TRAN n_and_3_pulse_width_after_pulse_in_period3_1 PARAM='n_and_3_fall_timing_3 - n_and_3_rise_timing_3'
.MEASURE TRAN n_and_3_pulse_width_after_pulse_in_period3_2 PARAM='n_and_3_fall_timing_4 - n_and_3_rise_timing_3'

*** injection timing之后三个周期内n_and_3的最大电压
.MEASURE TRAN n_and_3_max_vol_after_pulse_in_period1 MAX V(n_and_3) FROM=injection_timing_n1 TO='injection_timing_n1 + n_and_3_period'
.MEASURE TRAN n_and_3_max_vol_after_pulse_in_period2 MAX V(n_and_3) FROM='injection_timing_n1 + n_and_3_period' TO='injection_timing_n1 + 2*n_and_3_period'
.MEASURE TRAN n_and_3_max_vol_after_pulse_in_period3 MAX V(n_and_3) FROM='injection_timing_n1 + 2*n_and_3_period' TO='injection_timing_n1 + 3*n_and_3_period'

*** injection timing之后三个周期内n_and_4的最大电压
.MEASURE TRAN n_and_4_max_vol_after_pulse_in_period1 MAX V(n_and_4) FROM=injection_timing_n1 TO='injection_timing_n1 + n_and_3_period'
.MEASURE TRAN n_and_4_max_vol_after_pulse_in_period2 MAX V(n_and_4) FROM='injection_timing_n1 + n_and_3_period' TO='injection_timing_n1 + 2*n_and_3_period'
.MEASURE TRAN n_and_4_max_vol_after_pulse_in_period3 MAX V(n_and_4) FROM='injection_timing_n1 + 2*n_and_3_period' TO='injection_timing_n1 + 3*n_and_3_period'

*** injection timing之后一个周期内cd_3的rise_timing, fall_timing, pulse_width
.MEASURE TRAN cd_3_rise_timing_after_pulse_1 WHEN V(cd_3)=0.1 RISE=1 FROM=injection_timing_n1
.MEASURE TRAN cd_3_rise_timing_after_pulse_2 WHEN V(cd_3)=0.1 RISE=2 FROM=injection_timing_n1
.MEASURE TRAN cd_3_fall_timing_after_pulse_1 WHEN V(cd_3)=0.1 FALL=1 FROM=injection_timing_n1
.MEASURE TRAN cd_3_fall_timing_after_pulse_2 WHEN V(cd_3)=0.1 FALL=2 FROM=injection_timing_n1
.MEASURE TRAN cd_3_pulse_width_after_pulse_in_period1_1 PARAM='cd_3_fall_timing_after_pulse_1 - cd_3_rise_timing_after_pulse_1'
.MEASURE TRAN cd_3_pulse_width_after_pulse_in_period1_2 PARAM='cd_3_fall_timing_after_pulse_2 - cd_3_rise_timing_after_pulse_1'


*** injection timing之后两个周期内cd_4的rise_timing, fall_timing, pulse_width
.MEASURE TRAN cd_4_rise_timing_after_pulse_1 WHEN V(cd_4)=0.11 RISE=1 FROM=injection_timing_n1
.MEASURE TRAN cd_4_rise_timing_after_pulse_2 WHEN V(cd_4)=0.1 RISE=2 FROM=injection_timing_n1
.MEASURE TRAN cd_4_fall_timing_after_pulse_1 WHEN V(cd_4)=0.1 FALL=1 FROM=injection_timing_n1
.MEASURE TRAN cd_4_fall_timing_after_pulse_2 WHEN V(cd_4)=0.1 FALL=2 FROM=injection_timing_n1
.MEASURE TRAN cd_4_pulse_width_after_pulse_in_period1_1 PARAM='cd_4_fall_timing_after_pulse_1 - cd_4_rise_timing_after_pulse_1'
.MEASURE TRAN cd_4_pulse_width_after_pulse_in_period1_2 PARAM='cd_4_fall_timing_after_pulse_2 - cd_4_rise_timing_after_pulse_1'

*** 判断“11”错误：n_nand_3也出现波峰, 并使n_nand_4也出现波峰
*** 情况1 : n_and_3和n_and_4有波峰的情况下，n_nand_3和n_nand_4也有波峰 
*** 情况2 : n_and_3和n_and_4在注入后的一个周期内没有波峰，但n_nand_3和n_nand_4有波峰
*** 需要参数 : n_and_3, n_and_4, n_nand_3, n_nand_4在注入之后的pulse_width和max_vol
*** n_and_3的pulse width 和 max vol
.MEASURE TRAN n_and_3_rise_to_vdd_timing_after_pulse WHEN V(n_and_3)='vdd*0.8' FROM=injection_timing_n1
*** n_and_4的pulse width 和 max vol
.MEASURE TRAN n_and_4_rise_timing_after_pulse_1 WHEN V(n_and_4)=0.05 RISE=1 FROM=injection_timing_n1
.MEASURE TRAN n_and_4_fall_timing_after_pulse_1 WHEN V(n_and_4)=0.05 FALL=1 FROM=injection_timing_n1
.MEASURE TRAN n_and_4_pulse_width_after_pulse PARAM='n_and_4_fall_timing_after_pulse_1 - n_and_4_rise_timing_after_pulse_1'
.MEASURE TRAN n_and_4_rise_to_vdd_timing_after_pulse WHEN V(n_and_4)='vdd*0.8' FROM=injection_timing_n1

*** injection timing之后 n_nand_3和n_nand_4的max vol
.MEASURE TRAN n_nand_3_max_vol_after_pulse MAX V(n_nand_3) FROM=injection_timing_n1 TO='injection_timing_n1 + n_and_3_period'
.MEASURE TRAN n_nand_4_max_vol_after_pulse MAX V(n_nand_4) FROM=injection_timing_n1 TO='injection_timing_n1 + n_and_4_period'



VVDD  VDD  0 DC vdd               
VGND  GND  0 DC 0                  

.param simtime = 300n
.param pw1 = 3n  *it was 2n
.param pw2 = 3n
.param period1 = 4*pw1   *it was 6n
.param period2 = 4*pw1
.param latency1 = 5n
.param latency2 = latency1+2*pw1
.param latency3 = simtime
.param latency4 = simtime


*** 定义入力信号
VRESET RESET 0 PULSE(0 vdd 0n 0n 0n latency1 simtime)

VA A_n 0 PULSE(0 vdd latency1 0n 0n pw1 period1)
VB B_n 0 PULSE(0 vdd latency1 0n 0n pw1 period1)
VC C_n 0 PULSE(0 vdd latency1 0n 0n pw1 period1)

VA_p A_p 0 PULSE(0 vdd latency2 0n 0n pw1 period1)
VB_p B_p 0 PULSE(0 vdd latency2 0n 0n pw1 period1)
VC_p C_p 0 PULSE(0 vdd latency2 0n 0n pw1 period1)

VNA NA_n 0 PULSE(0 vdd latency3 0n 0n pw2 period2)
VNB NB_n 0 PULSE(0 vdd latency3 0n 0n pw2 period2)
VNC NC_n 0 PULSE(0 vdd latency3 0n 0n pw2 period2)

VNA_p NA_p 0 PULSE(0 vdd latency4 0n 0n pw2 period2)
VNB_p NB_p 0 PULSE(0 vdd latency4 0n 0n pw2 period2)
VNC_p NC_p 0 PULSE(0 vdd latency4 0n 0n pw2 period2)


* 波形的记述方法
* PWL(time1 volt1, time2 volt2, ...)  $ Lined change (time1 volt1), (time2 volt2) 
* PULSE(v1 v2 tdelay tr tf pw period) $ Square wave
* SIN(voffset vamp freq tdelay)       $ SIN wave

*$ Specify parameter set file
.include "/usr1/sai/design/rules/rohm180/spice/hspice/bu40n1.mdl"
.lib "/usr1/sai/design/rules/rohm180/spice/hspice/bu40n1.skw" NT
.lib "/usr1/sai/design/rules/rohm180/spice/hspice/bu40n1.skw" PT


*********************netlist_sim**********************

** Library name: error_tolerance
** Cell name: inv
** View name: schematic
.subckt inv gnd in out vdd
m1 out in gnd gnd N L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m0 out in vdd vdd P L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
.ends inv
** End of subcircuit definition.

** Library name: error_tolerance
** Cell name: inv_with_reset
** View name: schematic
.subckt inv_with_reset gnd in out reset vdd
m3 out reset gnd gnd N L=180e-9 W=1.5e-6 AD=3.00p AS=3.00p PD=7.00u PS=7.00u 
m1 out in gnd gnd N L=180e-9 W=1.5e-6 AD=3.00p AS=3.00p PD=7.00u PS=7.00u 
m2 out in net23 vdd P L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m0 net23 reset vdd vdd P L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
.ends inv_with_reset
** End of subcircuit definition.

** Library name: error_tolerance
** Cell name: inv2
** View name: schematic
.subckt inv2 gnd in out vdd
m1 out in gnd gnd N L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m0 out in vdd vdd P L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
.ends inv2
** End of subcircuit definition.

** Library name: error_tolerance
** Cell name: 3NAND_2_NP_error
** View name: schematic
xi63 gnd cd_3 net278 vdd inv
xi56 gnd cd_2 net234 vdd inv
xi47 gnd cd_1 net190 vdd inv
xi83 gnd cd_4 net0191 vdd inv
xi64 gnd net278 cd_3 reset vdd inv_with_reset
xi62 gnd net132 n_and_3 reset vdd inv_with_reset
xi61 gnd net261 p_and_3 reset vdd inv_with_reset
xi60 gnd cd_3 cd_n_3 reset vdd inv_with_reset
xi59 gnd net239 p_nand_3 reset vdd inv_with_reset
xi58 gnd net105 n_nand_3 reset vdd inv_with_reset
xi57 gnd net234 cd_2 reset vdd inv_with_reset
xi52 gnd net84 n_and_2 reset vdd inv_with_reset
xi49 gnd net217 p_and_2 reset vdd inv_with_reset
xi51 gnd cd_3 cd_n_2 reset vdd inv_with_reset
xi53 gnd net57 n_nand_2 reset vdd inv_with_reset
xi50 gnd net195 p_nand_2 reset vdd inv_with_reset
xi48 gnd net190 cd_1 reset vdd inv_with_reset
xi44 gnd net173 p_and_1 reset vdd inv_with_reset
xi43 gnd net36 n_and_1 reset vdd inv_with_reset
xi42 gnd cd_2 cd_n_1 reset vdd inv_with_reset
xi41 gnd net151 p_nand_1 reset vdd inv_with_reset
xi40 gnd net9 n_nand_1 reset vdd inv_with_reset
xi78 gnd net0191 cd_4 reset vdd inv_with_reset
xi75 gnd net0179 p_and_4 reset vdd inv_with_reset
xi74 gnd net0262 p_nand_4 reset vdd inv_with_reset
xi82 gnd cd_4 cd_n_4 reset vdd inv_with_reset
xi85 gnd net0180 n_and_4 reset vdd inv_with_reset
xi84 gnd net0152 n_nand_4 reset vdd inv_with_reset
m239 net261 p_and_3 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m238 net132 n_and_3 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m237 net132 cd_n_3 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m236 net261 cd_3 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m231 net105 cd_n_3 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m230 net239 cd_3 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m214 net239 p_nand_3 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m213 net105 n_nand_3 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m212 net84 n_and_2 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m211 net217 p_and_2 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m210 net217 cd_3 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m209 net84 cd_n_2 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m200 net195 cd_3 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m199 net57 cd_n_2 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m176 net57 n_nand_2 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m175 net195 p_nand_2 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m174 net36 n_and_1 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m113 net173 p_and_1 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m112 net36 cd_n_1 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m111 net173 cd_2 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m110 net9 cd_n_1 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m109 net151 cd_2 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m108 net9 n_nand_1 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m107 net151 p_nand_1 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m262 net0179 cd_4 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m268 net0152 cd_n_4 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m267 net0152 n_nand_4 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m261 net0262 cd_4 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m260 net0179 p_and_4 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m259 net0262 p_nand_4 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m270 net0180 n_and_4 vdd vdd P L=180e-9 W=1e-6 AD=2.00p AS=2.00p PD=6.00u PS=6.00u 
m269 net0180 cd_n_4 vdd vdd P L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m235 net132 n_and_2 net282 gnd N L=180e-9 W=2e-6 AD=0.52p AS=0.96p PD=4.52u PS=4.96u
m234 net283 n_and_2 net115 gnd N L=180e-9 W=3e-6 AD=1.44p AS=0.96p PD=6.96u PS=6.64u
m233 net282 n_and_2 net283 gnd N L=180e-9 W=2e-6 AD=0.2p AS=0.52p PD=4.2u PS=4.52u
m97 net261 p_and_2 net295 gnd N L=180e-9 W=2e-6 AD=0.52p AS=0.96p PD=4.52u PS=4.96u
m92 net295 p_and_2 net296 gnd N L=180e-9 W=2e-6 AD=0.2p AS=0.52p PD=4.2u PS=4.52u
m89 net296 p_and_2 net116 gnd N L=180e-9 W=3e-6 AD=1.44p AS=0.96p PD=6.96u PS=6.64u
m232 net115 cd_n_3 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m88 net116 cd_3 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m229 net284 n_and_2 net114 gnd N L=180e-9 W=2e-6 AD=0.96p AS=0.52p PD=4.96u PS=4.52u
m228 net105 n_nand_2 net284 gnd N L=180e-9 W=2e-6 AD=0.52p AS=0.96p PD=4.52u PS=4.96u
m98 net239 p_nand_2 net297 gnd N L=180e-9 W=2e-6 AD=0.52p AS=0.96p PD=4.52u PS=4.96u
m93 net297 p_and_2 net117 gnd N L=180e-9 W=2e-6 AD=0.96p AS=0.52p PD=4.96u PS=4.52u
m90 net117 p_and_2 net116 gnd N L=180e-9 W=3e-6 AD=1.44p AS=1.62p PD=6.96u PS=7.08u
m227 net114 n_and_2 net115 gnd N L=180e-9 W=3e-6 AD=1.44p AS=1.62p PD=6.96u PS=7.08u
m226 net105 n_nand_2 net113 gnd N L=180e-9 W=2e-6 AD=0.96p AS=0.96p PD=4.96u PS=4.96u
m225 net239 p_nand_2 net112 gnd N L=180e-9 W=2e-6 AD=0.96p AS=0.96p PD=4.96u PS=4.96u
m224 net113 n_nand_2 net114 gnd N L=180e-9 W=3e-6 AD=1.62p AS=1.14p PD=7.08u PS=6.76u
m94 net112 p_nand_2 net117 gnd N L=180e-9 W=3e-6 AD=1.62p AS=1.14p PD=7.08u PS=6.76u
m223 net105 n_and_2 net113 gnd N L=180e-9 W=2e-6 AD=0.32p AS=0.96p PD=4.32u PS=4.96u
m222 net239 p_and_2 net112 gnd N L=180e-9 W=2e-6 AD=0.32p AS=0.96p PD=4.32u PS=4.96u
m221 net105 n_nand_2 net246 gnd N L=180e-9 W=2e-6 AD=1.08p AS=0.96p PD=5.08u PS=4.96u
m220 net246 n_nand_2 net109 gnd N L=180e-9 W=3e-6 AD=0.48p AS=1.44p PD=6.32u PS=6.96u
m219 net239 p_nand_2 net245 gnd N L=180e-9 W=2e-6 AD=1.08p AS=0.96p PD=5.08u PS=4.96u
m95 net245 p_nand_2 net247 gnd N L=180e-9 W=3e-6 AD=0.48p AS=1.44p PD=6.32u PS=6.96u
m218 net109 n_nand_2 net115 gnd N L=180e-9 W=5e-6 AD=2.4p AS=1.9p PD=10.96u PS=10.76u
m91 net247 p_nand_2 net116 gnd N L=180e-9 W=5e-6 AD=2.4p AS=1.9p PD=10.96u PS=10.76u
m217 net105 n_and_2 net246 gnd N L=180e-9 W=2e-6 AD=0.96p AS=0.96p PD=4.96u PS=4.96u
m216 net246 n_and_2 net109 gnd N L=180e-9 W=2e-6 AD=0.96p AS=1.08p PD=4.96u PS=5.08u
m215 net239 p_and_2 net245 gnd N L=180e-9 W=2e-6 AD=0.96p AS=0.96p PD=4.96u PS=4.96u
m96 net245 p_and_2 net247 gnd N L=180e-9 W=2e-6 AD=0.96p AS=1.08p PD=4.96u PS=5.08u
m208 net299 p_and_1 net68 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m207 net288 n_and_1 net67 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m206 net287 n_and_1 net288 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m205 net84 n_and_1 net287 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m204 net217 p_and_1 net298 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m203 net298 p_and_1 net299 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m202 net68 cd_3 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m201 net67 cd_n_2 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m198 net195 p_nand_1 net300 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m197 net300 p_and_1 net69 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m196 net289 n_and_1 net66 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m195 net57 n_nand_1 net289 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m194 net69 p_and_1 net68 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m193 net66 n_and_1 net67 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m192 net57 n_nand_1 net65 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m191 net195 p_nand_1 net64 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m190 net65 n_nand_1 net66 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m189 net64 p_nand_1 net69 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m188 net57 n_and_1 net65 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m187 net195 p_and_1 net64 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m186 net195 p_nand_1 net201 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m185 net202 n_nand_1 net61 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m184 net201 p_nand_1 net203 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m183 net57 n_nand_1 net202 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m182 net61 n_nand_1 net67 gnd N L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m181 net203 p_nand_1 net68 gnd N L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m180 net195 p_and_1 net201 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m179 net201 p_and_1 net203 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m178 net202 n_and_1 net61 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m177 net57 n_and_1 net202 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m173 net293 c_n net19 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m172 net292 b_n net293 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m171 net36 a_n net292 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m170 net173 a_p net301 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m169 net301 b_p net302 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m168 net302 c_p net20 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m167 net19 cd_n_1 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m166 net20 cd_2 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m165 net294 b_n net18 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m164 net9 na_n net294 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m163 net151 na_p net303 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m162 net303 b_p net21 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m161 net21 c_p net20 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m160 net18 c_n net19 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m159 net9 na_n net17 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m158 net151 na_p net16 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m157 net17 nb_n net18 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m156 net16 nb_p net21 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m155 net9 a_n net17 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m154 net151 a_p net16 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m153 net158 nb_n net13 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m152 net151 na_p net157 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m151 net157 nb_p net159 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m150 net9 na_n net158 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m149 net13 nc_n net19 gnd N L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m148 net159 nc_p net20 gnd N L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m147 net158 b_n net13 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m146 net9 a_n net158 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m145 net151 a_p net157 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m144 net157 b_p net159 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m281 net0283 n_and_3 net0162 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m280 net0161 n_nand_3 net0162 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m279 net0155 n_nand_3 net0157 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m278 net0155 n_and_3 net0157 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m271 net0180 n_and_3 net0281 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m273 net0152 n_nand_3 net0155 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m255 net0262 p_and_3 net0160 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m254 net0262 p_nand_3 net0154 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m253 net0262 p_and_3 net0154 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m252 net0284 p_and_3 net0285 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m251 net0286 p_and_3 net0165 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m244 net0164 cd_4 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m275 net0152 n_nand_3 net0161 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m283 net0157 n_nand_3 net0163 gnd N L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m247 net0285 p_and_3 net0164 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m285 net0163 cd_n_4 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m246 net0165 p_and_3 net0164 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m258 net0179 p_and_3 net0284 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m257 net0262 p_nand_3 net0286 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m245 net0156 p_nand_3 net0164 gnd N L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m256 net0262 p_nand_3 net0160 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m282 net0282 n_and_3 net0163 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m274 net0152 n_and_3 net0161 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m272 net0152 n_and_3 net0155 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m277 net0281 n_and_3 net0282 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m250 net0160 p_nand_3 net0165 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m249 net0154 p_nand_3 net0156 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m248 net0154 p_and_3 net0156 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m284 net0162 n_and_3 net0163 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m276 net0152 n_nand_3 net0283 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m242 net278 net280 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m240 net278 net281 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m87 net234 net285 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m86 net234 net286 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m82 net190 net290 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m83 net190 net291 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m265 net0191 net0280 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m266 net0191 net0279 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m243 net278 n_nand_3 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m241 net278 n_and_3 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m85 net234 n_nand_2 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m84 net234 n_and_2 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m81 net190 n_nand_1 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m80 net190 n_and_1 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m264 net0191 n_nand_4 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m263 net0191 n_and_4 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
xi39 gnd p_nand_3 net280 vdd inv2
xi38 gnd p_and_3 net281 vdd inv2
xi55 gnd p_nand_2 net285 vdd inv2
xi54 gnd p_and_2 net286 vdd inv2
xi46 gnd p_nand_1 net290 vdd inv2
xi45 gnd p_and_1 net291 vdd inv2
xi81 gnd p_nand_4 net0279 vdd inv2
xi80 gnd p_and_4 net0280 vdd inv2


*********************netlist_sim**********************



.param current_duration = 0.1e-9  ***0.1ns

******************** injection timing delay ********************
.param injection_timing_n1 = simtime   ***n_and_3
.param injection_timing_n9 = simtime   ***n_nand_3
.param injection_timing_n2 = simtime   ***n pipeline internal node n2
.param injection_timing_n3 = simtime   ***n pipeline internal node n3
.param injection_timing_n4 = simtime   ***n pipeline internal node n4
.param injection_timing_n5 = simtime   ***n pipeline internal node n5
.param injection_timing_n6 = simtime   ***n pipeline internal node n6
.param injection_timing_n7 = simtime   ***n pipeline internal node n7
.param injection_timing_n8 = simtime   ***n pipeline internal node n8
.param injection_timing_p1 = simtime   ***n_and_3
.param injection_timing_p9 = simtime   ***n_nand_3
.param injection_timing_p2 = simtime   ***p pipeline internal node n2
.param injection_timing_p3 = simtime   ***p pipeline internal node n3
.param injection_timing_p4 = simtime   ***p pipeline internal node n4
.param injection_timing_p5 = simtime   ***p pipeline internal node n5
.param injection_timing_p6 = simtime   ***p pipeline internal node n6
.param injection_timing_p7 = simtime   ***p pipeline internal node n7
.param injection_timing_p8 = simtime   ***p pipeline internal node n8
.param injection_timing_cd = simtime   ***cd_3
******************** injection timing delay ********************



******************** injection node ********************
*** pulse i1 i2 delay rise fall pw period
i_n1 gnd net132 PULSE 0 current_height injection_timing_n1 0 0 current_duration simtime
i_n2 gnd net282 PULSE 0 current_height injection_timing_n2 0 0 current_duration simtime
i_n3 gnd net283 PULSE 0 current_height injection_timing_n3 0 0 current_duration simtime
i_n4 gnd net284 PULSE 0 current_height injection_timing_n4 0 0 current_duration simtime
i_n5 gnd net113 PULSE 0 current_height injection_timing_n5 0 0 current_duration simtime
i_n6 gnd net114 PULSE 0 current_height injection_timing_n6 0 0 current_duration simtime
i_n7 gnd net246 PULSE 0 current_height injection_timing_n7 0 0 current_duration simtime
i_n8 gnd net109 PULSE 0 current_height injection_timing_n8 0 0 current_duration simtime
i_n9 gnd net105 PULSE 0 current_height injection_timing_n9 0 0 current_duration simtime
i_p1 gnd net261 PULSE 0 current_height injection_timing_p1 0 0 current_duration simtime
i_p2 gnd net295 PULSE 0 current_height injection_timing_p2 0 0 current_duration simtime
i_p3 gnd net296 PULSE 0 current_height injection_timing_p3 0 0 current_duration simtime
i_p4 gnd net297 PULSE 0 current_height injection_timing_p4 0 0 current_duration simtime
i_p5 gnd net112 PULSE 0 current_height injection_timing_p5 0 0 current_duration simtime
i_p6 gnd net117 PULSE 0 current_height injection_timing_p6 0 0 current_duration simtime
i_p7 gnd net245 PULSE 0 current_height injection_timing_p7 0 0 current_duration simtime
i_p8 gnd net247 PULSE 0 current_height injection_timing_p8 0 0 current_duration simtime
i_p9 gnd net239 PULSE 0 current_height injection_timing_p9 0 0 current_duration simtime
i_cd gnd net278 PULSE 0 current_height injection_timing_cd 0 0 current_duration simtime
******************** injection node ********************



******************** pattern list ********************
net5  m228  net24  m229  net15  
net5  m223  net14  m224  net15  m227  net16  
net5  m226  net14  
net5  m221  net8  m216  net10  
net8  m220  net10  m218  net16  
net5  m217  net8  
net39  m235  net36  m233  net37  m234  net16  
******************** pattern list ********************
 
 
******************** area ratio ********************
* m216 : 0.0116
* m217 : 0.0116
* m218 : 0.0259
* m220 : 0.0164
* m221 : 0.0116
* m223 : 0.0116
* m224 : 0.0164
* m226 : 0.0116
* m227 : 0.0164
* m228 : 0.0116
* m229 : 0.0116
* m233 : 0.0116
* m234 : 0.0164
* m235 : 0.0116
* net10 : 0.0884
* net14 : 0.064
* net15 : 0.0683
* net16 : 0.1397
* net24 : 0.0138
* net36 : 0.0138
* net37 : 0.0307
* net39 : 0.0254
* net5 : 0.127
* net8 : 0.0921
******************** area ratio ********************

.END