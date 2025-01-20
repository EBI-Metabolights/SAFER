devtools::document('/Users/mjudge/Documents/GitHub/SAFERnmr')

    data.dir <- '/Users/mjudge/Documents/ftp_ebi/pipeline_runs_new/'
    
        unzip_studies(data.dir, exclude = c('1697751863','1697759923'))
        run.idx <- index_studies(data.dir, exclude = c('1697751863',
                                                       '1697759923',
                                                       '1713439191',
                                                       '1726497509',
                                                       '1726501646'))
  
    run.idx <- run.idx %>% filter(write_time >= '2024-09-23 15:00:00') %>% arrange(desc(write_time))
    xmat <- readRDS('/Users/mjudge/Downloads/MTBLS1_1r_noesypr1d_spectralMatrix.RDS')
      ppm <- xmat[1,]
      xmat <- xmat[-1,]
      # all.equal(xmat[1,], xmat[133,])
      xmat <- xmat[1:132,]
      sample.names <- rownames(xmat)
      
    run.id <- run.idx$local_path[1] # 1731960370
    # run.id <- "/Users/mjudge/Documents/ftp_ebi/pipeline_runs_new/1709742511"


load.data <- function(run.id='1731960370',
                      data.dir='/Users/mjudge/Documents/ftp_ebi/pipeline_runs_new/', 
                      maf.link='https://www.ebi.ac.uk/metabolights/ws/studies/MTBLS1/download/4ZWHUHHlKR?file=m_MTBLS1_metabolite_profiling_NMR_spectroscopy_v2_maf.tsv',
                      study='MTBLS1',
                      tmpdir='/Users/mjudge/Edison_Lab@UGA Dropbox/Michael Judge/MJ_UGA_Root/Scheduling/safer_manuscript/data/study_metabolites/',
                      chebi.key='/Users/mjudge/Documents/ftp_ebi/gissmo/gissmo2chebi_2024.xlsx'){

# Get the author-submitted annotations for mtbls1 ####

    study.dir <- paste0(tmpdir,study%>%tolower,'/')
    dir.create(study.dir,showWarnings = FALSE)
    if (!file.exists(paste0(study.dir,'maf.tsv'))){
      download.file(maf.link, destfile = paste0(study.dir,'maf.tsv'))
    }
      
    maf.data <- read.table(paste0(study.dir,'maf.tsv'), 
                           fill = TRUE, header = TRUE, 
                           sep = '\t', quote = "")
    maf.data$metabolite_identification <- maf.data$metabolite_identification %>% tolower
    
    maf.chebis <- maf.data$database_identifier %>% unique
      maf.chebis <- maf.chebis[-which(grepl('unknown', maf.chebis))] 
  
# Read results from SAFER ####

    res.dir <- paste0(data.dir, run.id,'/')
    scores <- readRDS(paste0(res.dir, "scores.RDS"))
      smat <- scores$ss.ref.mat
      mtbls.cmpds <- rownames(smat)

    xmat <- readRDS('/Users/mjudge/Downloads/MTBLS1_1r_noesypr1d_spectralMatrix.RDS')
      ppm <- xmat[1,]
      xmat <- xmat[-1,]
      # all.equal(xmat[1,], xmat[133,])
      xmat <- xmat[1:132,]
      
    
    # run.id <- "/Users/mjudge/Documents/ftp_ebi/pipeline_runs_new/1709742511"
      
  # Check lib.data
  
    lib.data.p <- readRDS(paste0(res.dir, 'lib.data.processed.RDS'))
    
  # What are the gissmo names that match to the author-annotated names (via common ChEBI) ####
    
    gissmo.cmpds <- readxl::read_xlsx(chebi.key)
    
    # source('/Users/mjudge/Documents/GitHub/MARIANA_setup_chron/R/add_chebiIDs.R') # on "no-zip" branch
    lib.data.p <- add_chebiIDs(lib.data = lib.data.p, key = gissmo.cmpds)
    
    in.author.list <- lapply(lib.data.p, function(x) x$chebi.id %in% maf.chebis) %>% unlist
    
    lib.data.p <- lib.data.p[in.author.list]
    
    gissmo <- data.frame(name = lib.data.p %>% lapply(function(x) x$compound.name) %>% unlist,
                         chebi = lib.data.p %>% lapply(function(x) x$chebi) %>% unlist) %>% 
      distinct(chebi, .keep_all = TRUE)

    chenomx.annots <- read.table('/Users/mjudge/Edison_Lab@UGA Dropbox/Michael Judge/MJ_UGA_Root/Scheduling/safer_manuscript/data/chenomx comparison/mtbls1 annotation evidence/chenomx/scoring_noGUI.csv', header = TRUE, sep = ',')

  # List all objects currently in the function's environment
    vars <- ls()
  # Optional: remove input variables or any others you don't want returned
    vars <- vars[!vars %in% c("x", "y")]
  # Return a named list of all remaining variables
    return(mget(vars))
}


data <- load.data()
list2env(data, envir = .GlobalEnv)

gissmo.overlap <- gissmo 
colnames(gissmo.overlap) <- c('names','chebis') # py script needs "names"
gissmo.overlap %>% write.csv('/Users/mjudge/Edison_Lab@UGA Dropbox/Michael Judge/MJ_UGA_Root/Scheduling/safer_manuscript/data/chenomx comparison/mtbls1 annotation evidence/safer/gissmo.author.overlap.csv',row.names = F)
# Run /Users/mjudge/Documents/GitHub/python_pptx_mj/csv2slides_function.py
# on that file to get slide template.

# Loop through the samples ####

      
  i <- 8

  i <- i + 1
  cmpd <- gissmo$name[i]
  
  # Get the compound of interest (row)
    rownum <- which(rownames(scores$ss.ref.mat) %in% cmpd)
    if (length(rownum) > 1){message('>1 reference for ', cmpd)}
    rownum <- rownum[1] # only look at first match
    
    row.scores <- scores$ss.ref.mat[rownum, ]
    # nds <- row.scores[order(row.scores, decreasing=TRUE) %>% .[1:5]] %>% names
    nds <- order(row.scores, decreasing=TRUE) %>% .[1:5]
    
  message(gissmo$name[i])
  browse_evidence(paste0(data.dir,'/',run.id), select.compounds = gissmo$name[i], select.samples = nds)
  # browse_evidence(paste0(data.dir,'/',run.id), select.compounds = gissmo$name[i])
  # browse_evidence(paste0(data.dir,'/',run.id))

  
  
  