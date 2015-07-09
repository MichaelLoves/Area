import math
import matplotlib.pyplot as plt
import numpy as np



L = 0.1
Q = 100.0
K = 0.00112838
e = 2.718281828

time = np.arange(0.0, 2.0, 0.01)
J = K*Q*pow(time/L, 0.5)*pow(e, -time/L)/L

plt.plot(time, J, color='red', linewidth=2)
plt.title('Injection Pulse Model')
plt.xlabel('Time (ns)')
plt.ylabel('Pulse current')

plt.xlim(-0.20, 2.00)
plt.ylim(0.00, 0.50)

plt.show()
