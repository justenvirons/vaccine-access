#
# Author: C. Scott Smith
# Date: 7/24/2020
# Purpose: Automate accessibility calculations using OTP, OSM and GTFS
#

import math
import time
import csv

from org.opentripplanner.scripting.api import OtpsEntryPoint

otp = OtpsEntryPoint.fromArgs(['--graphs', 'graphs',
                               '--router', 'ccdph'])

# Start timing the code
start_time = time.time()

# Stop timing the code
print("Elapsed time was %g seconds" % (time.time() - start_time))

# Get the default router
# CHANGE ROUTER NAME
router = otp.getRouter('ccdph')

totaliterations = 795*1*12*6 #795 origin census tracts * 1 model * 2 hour AM peak study period * 6, 10-minute intervals

# Load populations from origins and destinations files
points = otp.loadCSVPopulation('data/neighborhood_origins.csv', 'Y', 'X')#ORIGIN POINTS FILE NAME
dests = otp.loadCSVPopulation('data/neighborhood_dests.csv', 'Y', 'X')#DESTS POINTS FILE NAME

# aModeFileNameList = ['bus','rail','busrail']
# aModeList = ['BUS,WALK','RAIL,WALK','BUS,RAIL,WALK']

#aModeFileNameList = ['bus','rail','busrail']
#aModeList = ['BUS,WALK','RAIL,WALK','BUS,RAIL,WALK']

# aModeFileNameList = ['transit','transit','transit','transit']
# aModeList = ['WALK,TRANSIT','WALK,TRANSIT']

aModeFileNameList = ['transit']
aModeList = ['WALK,TRANSIT']

# Model 2: Public transit and walking (scheduled transit routes on street network; standard walk speed [1.3 m/s or 3 mph] and distance [1,609 m or 1 mile])
# Model 3: Public transit and walking (scheduled transit routes on street network; limited walk speed [0.9 m/s or 2.1 mph] and distance [804.7 m or 0.5 mile])
# Model 4: Public transit and walking (scheduled, wheelchair accessible transit route trips and stops on street network; standard walk speed [1.3 m/s or 3 mph] and distance [1,609 m or 1 mile])
# Model 5: Public transit and walking (scheduled, wheelchair accessible transit route trips and stops/stations on street network; limited walk speed [0.9 m/s or 2.1 mph] and distance [804.7 m or 0.5 mile])

# aModelList=['2','3','4','5']
# aWheelchairAccessList = [False,False,True,True]
# aWalkSpeedList = [1.34,0.94,1.34,0.94]
# aMaxDistList = [1609.34,804.67,1609.34,804.67]

aModelList=['1']
aWheelchairAccessList = [False]
aWalkSpeedList = [1.34]
aMaxDistList = [1609.34]

aModeParamNum = 0
aModelParamNum = 0
modelmode = "TRANSIT"

for aModeFileName in aModeFileNameList:
    for aModel in aModelList:
        # Create output file
        aoutputFileName = 'data/siteaccess_all_20210529_' + aModel +'_'+aModeFileName+'.csv'
        with open(aoutputFileName, 'w') as csvfile:
            fieldnamessum = ['modelmode', 'hour', 'minute', 'timestep', 'orig_id', 'dest_id', 'walk_distance','boardings', 'travel_time']
            # fieldnamessum = [ 'mode','model','wheelchair','walkspeed','maxdist','hours', 'minutes', 'timestep','orig_id', 'orig_lat','orig_lon','workers', 'count_dests', 'sum_walk_distance', 'sum_boardings','sum_travel_time','sum_networkaccess', 'sum_jobs' ]
            matrixCsvSum = csv.DictWriter(csvfile,lineterminator='\n', fieldnames=fieldnamessum)
            matrixCsvSum.writeheader()
            # Create a default request for a given time
            # Start Loop
            origin_num=0
            maxtimesteps = [7200] #30 minute
            # maxtimesteps = [3600]  # 15 minute; 30 minute; 45 minute; 60 minute max travel times
            req = otp.createRequest()
            for calc_hour in range(8,9):
                for calc_min in range (0,6):
                    calc_min=calc_min*10
                    for timestep in maxtimesteps:
                        req.setDateTime(2021, 5, 29, calc_hour, calc_min, 00)  # set departure time
                        req.setMaxTimeSec(timestep) # set a limit to maximum travel time (seconds)
                        req.setWheelchairAccessible(aWheelchairAccessList[aModelParamNum])
                        req.setMaxWalkDistance(aMaxDistList[aModelParamNum])
                        req.setWalkSpeedMs(aWalkSpeedList[aModelParamNum])
                        req.setModes(aModeList[aModeParamNum]) #set mode(s) of interest
                        for origin in points:
                            origin_num=origin_num+1
                            print('(Mode ' + str(aModeParamNum) + ',Model ' + str(aModelParamNum) + ') Processing iteration ' + str(origin_num) + ' of ' + str(totaliterations))
                            req.setOrigin(origin)
                            spt = router.plan(req)

                            if spt is None:continue

                            # Evaluate the SPT from each origin to all destination points in population
                            result = spt.eval(dests)

                            # Calculate values for summary variables
                            for r in result:
                                adest_id = r.getIndividual().getStringData('DESTID')
                                walk_distance = r.getWalkDistance()
                                boardings = r.getBoardings()
                                travel_time = r.getTime()

                              # Add a new row of results in summary CSV output

                                matrixCsvSum.writerow(
                                    {'modelmode': modelmode, 'hour': calc_hour, 'minute': calc_min, 'timestep': timestep,
                                     'orig_id': origin.getStringData('ORIGID'),
                                     'dest_id': adest_id, 'walk_distance': walk_distance, 'boardings': boardings,
                                     'travel_time': travel_time})

                            # matrixCsvSum.writerow({'mode':aModeFileName,'model':aModel,'wheelchair':aWheelchairAccessList[aModelParamNum],'walkspeed':aWalkSpeedList[aModelParamNum],'maxdist':aMaxDistList[aModelParamNum],'hours':calc_hour, 'minutes':calc_min, 'timestep': timestep, 'orig_id':origin.getStringData('ORIGID'), 'orig_lat':spt.getSnappedOrigin().getLat(),'orig_lon':spt.getSnappedOrigin().getLon(),'workers': origin.getStringData('Workers'),'count_dests': count_dests, 'sum_walk_distance': sum_walk_distance , 'sum_boardings':sum_boardings, 'sum_travel_time':sum_travel_time, 'sum_networkaccess':sum_networkaccess, 'sum_jobs':sum_jobs})
        aModelParamNum = aModelParamNum + 1
    aModelParamNum = 0
    aModeParamNum = aModeParamNum + 1


# Stop timing the code
print("Elapsed time was %g seconds" % (time.time() - start_time))