suppressPackageStartupMessages(library(data.table))
suppressPackageStartupMessages(library(plyr))
suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(modelr))


command_args <-commandArgs(trailingOnly = TRUE)
if(command_args[1] != "--city_name"){
  stop("You need to provide a city using --city_name!")
}
city_name <-command_args[2]

fingerprints <- fread(paste0("results/park_fingerprints_",city_name,".csv"))


THRESHOLD_LM_SPACES <- 0.05
THRESHOLD_LM_ELEMENTS <- 2


fingerprints[is.na(fingerprints)] <- 0

fingerprints <- fingerprints[name != '']
fingerprints[,name:=as.factor(name)]
fingerprints[,osm_id:=as.factor(osm_id)]


fingerprints_melt <- melt(fingerprints,id.vars = c('osm_id','name','area','total_nodes'))

fingerprints_area_melt <- fingerprints_melt[fingerprints_melt[,variable %in% c('physical_area','environmental_area','nature_area','social_area','cultural_area')]]
fingerprints_area_melt[,log_value:=log(1+value,base=2)]
fingerprints_area_melt[,log_area:=log(1+area,base=2)]
#fingerprints_area_melt[,score:=log_value/log_area]
#fingerprints_area_melt <- fingerprints_area_melt[!is.na(score)]


fingerprints_area_melt_cultural_residuals <- fingerprints_area_melt[variable=='cultural_area'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_area_melt[value>THRESHOLD_LM_SPACES & variable=='cultural_area']),var = 'residuals')
fingerprints_area_melt_physical_residuals <-fingerprints_area_melt[variable=='physical_area'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_area_melt[value>THRESHOLD_LM_SPACES&variable=='physical_area']),var = 'residuals')
fingerprints_area_melt_nature_residuals  <-fingerprints_area_melt[variable=='nature_area'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_area_melt[value>THRESHOLD_LM_SPACES& variable=='nature_area']),var = 'residuals')
fingerprints_area_melt_social_residuals <-  fingerprints_area_melt[ variable=='social_area'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_area_melt[value>THRESHOLD_LM_SPACES & variable=='social_area']),var = 'residuals')
fingerprints_area_melt_environmental_residuals <- fingerprints_area_melt[variable=='environmental_area'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_area_melt[value>THRESHOLD_LM_SPACES & variable=='environmental_area']),var = 'residuals') 

fingerprints_area_melt <- rbindlist(list(fingerprints_area_melt_cultural_residuals,fingerprints_area_melt_physical_residuals,fingerprints_area_melt_nature_residuals,fingerprints_area_melt_social_residuals,fingerprints_area_melt_environmental_residuals))
fingerprints_area_melt[,residuals_zeta:=scale(residuals, center = TRUE, scale = TRUE)]


fingerprints_area_melt[,variable:=gsub("_area", "", variable)]
fingerprints_area_melt[,variable:=as.factor(variable)]


fingerprints_nodes_melt <- fingerprints_melt[fingerprints_melt[,variable %in% c('physical_nodes','environmental_nodes','nature_nodes','social_nodes','cultural_nodes')]]
fingerprints_nodes_melt[,log_area:=log(1+area,base=2)]
fingerprints_nodes_melt[,log_value:=log(1+value,base=2)]
fingerprints_nodes_melt[,log_nodes:=log(1+total_nodes,base=2)]
fingerprints_nodes_melt <- fingerprints_nodes_melt[!is.na(log_value)]

fingerprints_nodes_melt_cultural_residuals <- fingerprints_nodes_melt[variable=='cultural_nodes'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_nodes_melt[value>THRESHOLD_LM_ELEMENTS & variable=='cultural_nodes']),var = 'residuals')
fingerprints_nodes_melt_physical_residuals <-fingerprints_nodes_melt[variable=='physical_nodes'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_nodes_melt[value>THRESHOLD_LM_ELEMENTS&variable=='physical_nodes']),var = 'residuals')
fingerprints_nodes_melt_nature_residuals  <-fingerprints_nodes_melt[variable=='nature_nodes'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_nodes_melt[value>THRESHOLD_LM_ELEMENTS& variable=='nature_nodes']),var = 'residuals')
fingerprints_nodes_melt_social_residuals <-  fingerprints_nodes_melt[ variable=='social_nodes'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_nodes_melt[value>THRESHOLD_LM_ELEMENTS & variable=='social_nodes']),var = 'residuals')
fingerprints_nodes_melt_environmental_residuals <- fingerprints_nodes_melt[variable=='environmental_nodes'] %>% add_residuals(lm(log_value~log_area,data=fingerprints_nodes_melt[value>THRESHOLD_LM_ELEMENTS & variable=='environmental_nodes']),var = 'residuals') 

fingerprints_nodes_melt <- rbindlist(list(fingerprints_nodes_melt_cultural_residuals,fingerprints_nodes_melt_physical_residuals,fingerprints_nodes_melt_nature_residuals,fingerprints_nodes_melt_social_residuals,fingerprints_nodes_melt_environmental_residuals))
fingerprints_nodes_melt[,residuals_zeta:=scale(residuals, center = TRUE, scale = TRUE)]

fingerprints_nodes_melt[,variable:=gsub("_nodes", "", variable)]

regression_area=function(dt_var){
  reg_fun<-lm(formula=log_value~log_area,data = dt_var) 
  slope<-round(coef(reg_fun)[2],3)  
  intercept <- round(coef(reg_fun)[1],3) 
  R2<-round(as.numeric(summary(reg_fun)[8]),3)

  return(c(intercept,slope,R2))
}
regression_nodes=function(dt_var){
  reg_fun<-lm(formula=log_value~log_nodes,data = dt_var ) #regression function
  slope<-round(coef(reg_fun)[2],3)   
  R2<-round(as.numeric(summary(reg_fun)[8]),3)
  
  return(c(slope,R2))
}


regression_nodes_value_area <-ddply(fingerprints_nodes_melt[value>THRESHOLD_LM_ELEMENTS],"variable",regression_area)
colnames(regression_nodes_value_area)<-c ("variable","intercept","slope","R2")
regression_nodes_value_area <- as.data.table(regression_nodes_value_area)


regression_area_value_area <-ddply(fingerprints_area_melt[value>THRESHOLD_LM_SPACES],"variable",regression_area)
colnames(regression_area_value_area)<-c ("variable","intercept","slope","R2")
regression_area_value_area <- as.data.table(regression_area_value_area)


all_residuals <- merge(fingerprints_nodes_melt,fingerprints_area_melt,by=c('osm_id','variable','name'),suffixes = c(".elements",".spaces"))
all_residuals[,combined_score:=(residuals_zeta.elements+residuals_zeta.spaces)/2]

score_file <- paste0('results/park_scores_',city_name,'.csv')
fwrite(all_residuals[,.(osm_id,variable,name,combined_score)],score_file)
print(paste0("Written park activity scores of ", city_name, " to ", score_file))