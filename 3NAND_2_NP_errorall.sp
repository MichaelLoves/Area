.TITLE 3NAND_2_NP_errorall

.OPTION POST=2 POST_VERSION=2001  $ Generate .tr0 file
.OPTION MTTHRESH=10               $ Multi-core operation if >10 transitor
.OPTION PROBE                    $ Nanosim requires this line
.PROBE V(*) I(I69) I(I70) I(I71) I(I72) I(I73)      $ Nanosim requires to specify output node

.TEMP = 27                    
.param mvdd = 0.6 
.TRAN 1p simtime sweep currentdelay72 10n 15n 0.1n
.param currentheight = 10e-6   ***100e-6 = 0.1mA

VVDD  VDD  0 DC mvdd               
VGND  GND  0 DC 0                  

.param simtime = 200n
.param pw1 = simtime *2n  *it was 2n
.param pw2 = simtime
.param period1 = simtime *4*pw1   it was 6n
.param period2 = simtime
.param latency1 = 5n
.param latency2 = 5n *latency1+2*pw1
.param latency3 = simtime
.param latency4 = simtime


VRESET RESET 0 PULSE(0 mvdd 0n 0n 0n latency1 simtime)

VA A_n 0 PULSE(0 mvdd latency1 0n 0n pw1 period1)
VB B_n 0 PULSE(0 mvdd latency1 0n 0n pw1 period1)
VC C_n 0 PULSE(0 mvdd latency1 0n 0n pw1 period1)


VA_p A_p 0 PULSE(0 mvdd latency2 0n 0n pw1 period1)
VB_p B_p 0 PULSE(0 mvdd latency2 0n 0n pw1 period1)
VC_p C_p 0 PULSE(0 mvdd latency2 0n 0n pw1 period1)

VNA NA_n 0 PULSE(0 mvdd latency3 0n 0n pw2 period2)
VNB NB_n 0 PULSE(0 mvdd latency3 0n 0n pw2 period2)
VNC NC_n 0 PULSE(0 mvdd latency3 0n 0n pw2 period2)

VNA_p NA_p 0 PULSE(0 mvdd latency4 0n 0n pw2 period2)
VNB_p NB_p 0 PULSE(0 mvdd latency4 0n 0n pw2 period2)
VNC_p NC_p 0 PULSE(0 mvdd latency4 0n 0n pw2 period2)



* PWL(time1 volt1, time2 volt2, ...)  $ Lined change (time1 volt1), (time2 volt2) 
* PULSE(v1 v2 tdelay tr tf pw period) $ Square wave
* SIN(voffset vamp freq tdelay)       $ SIN wave

*$ Specify parameter set file
.include "../../../../../rules/rohm180/spice/hspice/bu40n1.mdl"
.lib "../../../../../rules/rohm180/spice/hspice/bu40n1.skw" NT
.lib "../../../../../rules/rohm180/spice/hspice/bu40n1.skw" PT


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
m235 net132 n_nand_2 net282 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m234 net283 n_nand_2 net115 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m233 net282 n_nand_2 net283 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m97 net261 p_nand_2 net295 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m92 net295 p_nand_2 net296 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m89 net296 p_nand_2 net116 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m232 net115 cd_n_3 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m88 net116 cd_3 gnd gnd N L=180e-9 W=4e-6 AD=8.00p AS=8.00p PD=12.00u PS=12.00u 
m229 net284 n_nand_2 net114 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m228 net105 n_and_2 net284 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m98 net239 p_and_2 net297 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m93 net297 p_nand_2 net117 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m90 net117 p_nand_2 net116 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m227 net114 n_nand_2 net115 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m226 net105 n_and_2 net113 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m225 net239 p_and_2 net112 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m224 net113 n_and_2 net114 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m94 net112 p_and_2 net117 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m223 net105 n_nand_2 net113 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m222 net239 p_nand_2 net112 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m221 net105 n_and_2 net246 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m220 net246 n_and_2 net109 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m219 net239 p_and_2 net245 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m95 net245 p_and_2 net247 gnd N L=180e-9 W=3e-6 AD=6.00p AS=6.00p PD=10.00u PS=10.00u 
m218 net109 n_and_2 net115 gnd N L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m91 net247 p_and_2 net116 gnd N L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m217 net105 n_nand_2 net246 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m216 net246 n_nand_2 net109 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m215 net239 p_nand_2 net245 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m96 net245 p_nand_2 net247 gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
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
m242 net278 net280 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m240 net278 net281 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m87 net234 net285 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m86 net234 net286 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m82 net190 net290 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m83 net190 net291 vdd vdd P L=180e-9 W=5e-6 AD=10.00p AS=10.00p PD=14.00u PS=14.00u 
m243 net278 n_nand_3 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m241 net278 n_and_3 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m85 net234 n_nand_2 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m84 net234 n_and_2 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m81 net190 n_nand_1 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
m80 net190 n_and_1 gnd gnd N L=180e-9 W=2e-6 AD=4.00p AS=4.00p PD=8.00u PS=8.00u 
xi24 gnd p_nand_3 net280 vdd inv2
xi1 gnd p_and_3 net281 vdd inv2
xi55 gnd p_nand_2 net285 vdd inv2
xi54 gnd p_and_2 net286 vdd inv2
xi46 gnd p_nand_1 net290 vdd inv2
xi45 gnd p_and_1 net291 vdd inv2


*** pulse i1 i2 delay rise fall pw period
*** I69 N_and
*** I70 N_nand
*** I71 P_and
*** I72 P_nand
*** I73 CD_3

.param currentduration = 0.1e-9  ***0.1ns

.param currentdelay73 = simtime   ***CD_3
.param currentdelay72 = simtime   ***P_nand_3
.param currentdelay71 = simtime   ***P_and_3
.param currentdelay70 = simtime   ***N_nand_3
.param currentdelay69 = simtime   ***N_and_3

i73 gnd net278 PULSE 0 currentheight currentdelay73 0 0 currentduration simtime
i72 gnd net239 PULSE 0 currentheight currentdelay72 0 0 currentduration simtime
i71 gnd net261 PULSE 0 currentheight currentdelay71 0 0 currentduration simtime
i70 gnd net105 PULSE 0 currentheight currentdelay70 0 0 currentduration simtime
i69 gnd net132 PULSE 0 currentheight currentdelay69 0 0 currentduration simtime


.END
