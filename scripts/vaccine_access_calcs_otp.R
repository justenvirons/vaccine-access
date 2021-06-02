## Script name: vaccine_access_calcs_otp.R
## Purpose of script: direct measures of access to vaccine providers
## Author: C. Scott Smith, PhD AICP
## Date Created: 2021-05-28
## Date Last Updated: 2021-05-28
## Email: christopher.smith@cookcountyhealth.org


# activate R packages -----------------------------------------------------
install.packages("opentripplanner") # Install Package
library(opentripplanner)            # Load Package
library(dplyr)
library(tidyverse)
library(sf)

# create otp objects ------------------------------------------------------
# https://docs.ropensci.org/opentripplanner/articles/opentripplanner.html
# save latest jar to designated location 
path_data <- file.path(getwd(), "otp/graphs/ccdph")
path_otp <- otp_dl_jar(path_data, cache = FALSE)

log1 <- otp_build_graph(otp = path_otp, dir = path_data) 

otp_ccdph <- otp_setup(otp = path_otp, 
                 dir = path_data,
                 router = "ccdph")

otp_ccdph <- otp_setup(otp = path_otp, 
                       dir = path_data)

otp_stop()


routingOptions <- otp_routing_options()

address_single <- tibble(singlelineaddress = c(
  "11 Wall St, NY, NY",
  "600 Peachtree Street NE, Atlanta, Georgia"
))

osm_s1 <- geo(
  address = address_single$singlelineaddress, 
  method = "census",
  lat = latitude, 
  long = longitude
)

path_data <- file.path(getwd(), "otp")
path_otp <- otp_dl_jar(path_data, cache = TRUE)

log_setup_ccdph <- otp_setup(otp = path_otp, 
                             dir = path_data, 
                             router="ccdph", 
                             port = 8801, 
                             securePort = 8802, 
                             memory = 10240)

otpcon <- otp_connect(timezone = "America/Chicago", 
                      port = 9080)

route <- otp_plan(otpcon, 
                  # mode=c('WALK', 'TRANSIT'),
                  mode=c('WALK'),
                  maxWalkDistance = 810,
                  numItineraries = 1,
                  ncores = 3,
                  arriveBy = FALSE,
                  get_geometry = TRUE,
                  fromPlace = c(-87.72720, 41.91454),
                  toPlace = c(-87.68394, 41.88388),
                  date_time = as.POSIXct(strptime("2021-5-15 14:14",
                                                  "%Y-%m-%d %H:%M")))

route <- route %>% st_as_sf()
plot(route,
     max.plot = 1)

locations <- osm_geocode("museums in Chicago, IL", limit=10)

locations <- otp_geocode(otpcon,
                         corners=FALSE,
                         query="Jackson")

otp_stop()

lsoa <- sf::st_read("https://github.com/ropensci/opentripplanner/releases/download/0.1/centroids.gpkg",
                    stringsAsFactors = FALSE)


census_tracts <- st_read("layers/CC_CensusTracts_geom.shp") %>%
  select(geo_code = GEOID,
         geo_name = NAME) %>%
  st_centroid()
census_tracts <- st_transform(census_tracts, crs=4326)
st_crs(census_tracts)

providers <- st_read("layers/inventory_provider.shp") %>%
  filter(date == max(date),
         provno=="0040169485") %>%
  select(org_name = orgname,
         loc_name = locname,
         geo_code = provno)
providers <- st_transform(providers, crs=4326)


routes <- otp_plan(otpcon = otpcon,
                   fromPlace = census_tracts,
                   toPlace = providers,
                   mode=c('CAR'),
                   maxWalkDistance = 810,
                   numItineraries = 1,
                   ncores = 3,
                   arriveBy = FALSE,
                   get_geometry = FALSE)
