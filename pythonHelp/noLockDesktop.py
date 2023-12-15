import ctypes

ctypes.windll.kernel32.SetThreadExecutionState(0x80000002) #this will prevent the screen saver or sleep. 

## your code and operations 

ctypes.windll.kernel32.SetThreadExecutionState(0x80000000) #set the setting back to normal
quit()
