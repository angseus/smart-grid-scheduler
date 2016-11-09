# Same X-axis for all graphs
x_data = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143]

#######################
### With scheduling ###
#######################
# Threshold 1200 - used as standard threshold
threshold_1200 = [0, 0, 600, 1360, 760, 760, 20, 1130, 1130, 780, 1200, 1200, 0, 760, 760, 760, 600, 600, 150, 930, 930, 930, 620, 620, 20, 760, 800, 1240, 1240, 950, 190, 950, 950, 950, 790, 790, 190, 1840, 1840, 2600, 1550, 1550, 190, 950, 950, 950, 940, 940, 540, 1140, 1140, 1300, 2500, 1300, 540, 990, 1150, 1150, 1890, 1850, 1040, 1760, 1850, 1700, 1540, 1450, 0, 760, 760, 760, 600, 600, 0, 760, 760, 760, 600, 600, 2500, 3260, 3260, 3260, 3100, 3100, 3350, 4110, 4110, 4110, 3950, 3950, 2500, 3260, 3260, 3260, 3100, 3100, 2500, 3260, 3260, 3260, 3100, 3100, 0, 760, 760, 760, 600, 600, 0, 760, 760, 760, 600, 620, 1220, 970, 1130, 780, 2120, 2280, 0, 760, 760, 760, 600, 600, 0, 760, 760, 760, 600, 600, 0, 760, 760, 760, 600, 600, 0, 760, 760, 760, 600, 600]

# Threshold 600
threshold_600 = [0, 0, 160, 760, 1360, 1200, 20, 970, 970, 780, 1360, 1360, 0, 160, 160, 760, 1200, 1200, 150, 330, 330, 930, 1220, 1220, 20, 160, 200, 1240, 1840, 1550, 190, 350, 350, 950, 1390, 1390, 190, 1840, 1840, 2600, 1550, 1550, 190, 350, 350, 950, 1540, 1740, 540, 540, 540, 2500, 1900, 1900, 540, 390, 550, 1150, 2290, 2450, 1040, 1160, 1250, 1700, 2140, 2050, 0, 160, 160, 760, 1200, 1200, 0, 160, 160, 760, 1200, 1200, 2500, 2660, 2660, 3260, 3700, 3700, 3350, 3510, 3510, 4110, 4550, 4550, 2500, 2660, 2660, 3260, 3700, 3700, 2500, 2660, 2660, 3260, 3700, 3700, 0, 160, 160, 760, 1200, 1200, 0, 160, 160, 760, 1200, 2420, 20, 970, 970, 780, 2280, 2280, 0, 160, 160, 760, 1200, 1200, 0, 160, 160, 760, 1200, 1200, 0, 160, 160, 760, 1200, 1200, 0, 160, 160, 760, 1200, 1200]

# Threshold 2000
threshold_2000 = [0, 0, 1360, 1360, 760, 0, 20, 1730, 1730, 780, 600, 600, 0, 1360, 1360, 760, 0, 0, 150, 1530, 1530, 930, 20, 20, 20, 1360, 1400, 1400, 640, 190, 190, 1550, 1550, 950, 190, 190, 190, 1840, 1840, 2600, 1550, 1550, 190, 1550, 1550, 950, 340, 540, 540, 1900, 1900, 1740, 700, 1140, 540, 1750, 1750, 1150, 1090, 1090, 1040, 2360, 2450, 1700, 940, 850, 0, 1360, 1360, 760, 0, 0, 0, 1360, 1360, 760, 0, 0, 2500, 3860, 3860, 3260, 2500, 2500, 3350, 4710, 4710, 4110, 3350, 3350, 2500, 3860, 3860, 3260, 2500, 2500, 2500, 3860, 3860, 3260, 2500, 2500, 0, 1360, 1360, 760, 0, 0, 0, 1360, 1360, 760, 0, 1220, 20, 1730, 1730, 780, 1520, 1520, 0, 1360, 1360, 760, 0, 0, 0, 1360, 1360, 760, 0, 0, 0, 1360, 1360, 760, 0, 0, 0, 1360, 1360, 760, 0, 0]

##########################
### Without scheduling ###
##########################
no_scheduling = [0, 0, 600, 760, 1360, 760, 20, 970, 1570, 780, 1360, 760, 0, 0, 600, 760, 1360, 760, 150, 170, 770, 930, 1380, 780, 20, 0, 640, 2250, 2850, 1800, 1040, 1040, 1640, 3450, 4050, 3450, 2690, 4340, 4940, 5100, 4050, 3450, 2690, 2690, 3290, 3450, 5050, 4450, 3890, 3890, 4490, 4650, 5600, 3800, 3040, 2890, 3490, 1150, 2650, 1850, 190, 150, 840, 850, 1450, 760, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 780, 1220, 970, 1570, 780, 2280, 1680, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 760, 0, 0, 600, 760, 1360, 760]

def calculate_average(array):
	sum = 0
	for elem in array:
		sum += elem
	average = float(sum) / float(len(array))
	return average

def calculate_par(array):
	average = calculate_average(array)
	peak = max(array)
	return (float(peak) / float(average))

if __name__ == '__main__':
	print("# Threshold 1200 #")
	print("Average: " + str(calculate_average(threshold_1200)))
	print("Max / Peak: " + str(max(threshold_1200)))
	print("PAR: " + str(calculate_par(threshold_1200)))
	print("")
	print("# Threshold 600 #")
	print("Average: " + str(calculate_average(threshold_600)))
	print("Max / Peak: " + str(max(threshold_600)))
	print("PAR: " + str(calculate_par(threshold_600)))
	print("")
	print("# Threshold 2000 #")
	print("Average: " + str(calculate_average(threshold_2000)))
	print("Max / Peak: " + str(max(threshold_2000)))
	print("PAR: " + str(calculate_par(threshold_2000)))
	print("")
	print("# No scheduling #")
	print("Average: " + str(calculate_average(no_scheduling)))
	print("Max / Peak: " + str(max(no_scheduling)))
	print("PAR: " + str(calculate_par(no_scheduling)))