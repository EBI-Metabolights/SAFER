add_chebiIDs <- function(lib.data, key){

  # Get the compound names and data
  
    lapply(lib.data, function(x){x$tag})
  
    lib.data <- lapply(lib.data, function(x){
      
      # x$info.row$Entry.ID %>% print

      match <- key$metabolite_identification %in% x$compound.name
      
      if (any(match)){
        
        x$chebi.id <- key$database_identifier[match] %>% .[1]
        
      } else {
        
          x$chebi.id <- NA
      
      }
      
       return(x)
      
    })
  
    
  # 
  
  return(lib.data)
}
