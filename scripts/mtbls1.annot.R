devtools::document('/Users/mjudge/Documents/GitHub/SAFERnmr')

# Read data ####
# tmpdir <- '/Users/mjudge/Documents/ftp_ebi/pipeline_runs_new/1731870877/'
tmpdir <- '/Users/mjudge/Documents/ftp_ebi/pipeline_runs_new/1731960370/'

scores <- readRDS(paste0(tmpdir, "scores.RDS"))
smat <- scores$ss.ref.mat
mtbls.cmpds <- rownames(smat)
chenomx.annots <- read.table('/Users/mjudge/Edison_Lab@UGA Dropbox/Michael Judge/MJ_UGA_Root/Scheduling/safer_manuscript/data/chenomx comparison/mtbls1 annotation evidence/chenomx/scoring_noGUI.csv', header = TRUE, sep = ',')

# Check lib.data

lib.data.p <- readRDS(paste0(tmpdir, 'lib.data.processed.RDS'))

# Get the author-submitted annotations for mtbls1 ####

    maf.link <- 'https://www.ebi.ac.uk/metabolights/ws/studies/MTBLS1/download/4ZWHUHHlKR?file=m_MTBLS1_metabolite_profiling_NMR_spectroscopy_v2_maf.tsv'
    study <- 'MTBLS1'
    tmpdir <- '/Users/mjudge/Edison_Lab@UGA Dropbox/Michael Judge/MJ_UGA_Root/Scheduling/safer_manuscript/data/study_metabolites/'
    study.dir <- paste0(tmpdir,study%>%tolower,'/')
    dir.create(study.dir)
    # download.file(maf.link, destfile = paste0(study.dir,'maf.tsv'))
    maf.data <- read.table(paste0(study.dir,'maf.tsv'), 
                           fill = TRUE, header = TRUE, 
                           sep = '\t', quote = "")
    maf.data$metabolite_identification <- maf.data$metabolite_identification %>% tolower
    
    maf.chebis <- maf.data$database_identifier %>% unique
      maf.chebis <- maf.chebis[-which(grepl('unknown', maf.chebis))] 

# What are the gissmo names that match to the author-annotated names (via common ChEBI) ####
  
      gissmo.cmpds <- readxl::read_xlsx('/Users/mjudge/Documents/ftp_ebi/gissmo/gissmo2chebi_2024.xlsx')
      
      source('/Users/mjudge/Documents/GitHub/MARIANA_setup_chron/R/add_chebiIDs.R') # on "no-zip" branch
      lib.data.p <- add_chebiIDs(lib.data = lib.data.p, key = gissmo.cmpds)
      
      in.author.list <- lapply(lib.data.p, function(x) x$chebi.id %in% maf.chebis) %>% unlist
      
      lib.data.p <- lib.data.p[in.author.list]
      
      gissmo <- data.frame(name = lib.data.p %>% lapply(function(x) x$compound.name) %>% unlist,
                           chebi = lib.data.p %>% lapply(function(x) x$chebi) %>% unlist) %>% 
        distinct(chebi, .keep_all = TRUE)

# Pull evidence 
# Read SAFER Results ####
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
      
    run.id <- run.idx$local_path[1]
    # run.id <- "/Users/mjudge/Documents/ftp_ebi/pipeline_runs_new/1709742511"
      
# Loop through the samples ####

  i <- 0
  i <- 29
  
  i <- i + 1
  id <- gissmo$chebi[i]
  
  samp <- chenomx.annots$sample[chenomx.annots$chebi %in% id]
  if (!is.null(samp)){
    select.samples <- samp 
  } else {
    select.samples <- NULL
  }
  sample.names <- rownames(xmat)
    nds <- lapply(select.samples, function(x) which(grepl(pattern = x, sample.names))) %>% unlist # %>% sample.names[.]
  message(gissmo$name[i])
  browse_evidence(run.id, select.compounds = gissmo$name[i], select.samples = nds)
  # browse_evidence(run.id, select.compounds = gissmo$name[i])
  
# Sum up Chenomx table ####

  sum(chenomx.annots$reasonable.nonsinglet > 0, na.rm = TRUE)
  sum(chenomx.annots$green.peaks > 0, na.rm = TRUE)
  sum(chenomx.annots$reasonable.singlet > 0 & chenomx.annots$reasonable.nonsinglet == 0, na.rm = TRUE)
  
    
  
# Describe objects

describe_rds <- function(file_path) {
  # Check if file exists
  if (!file.exists(file_path)) {
    stop(paste("File not found:", file_path))
  }
  
  # Read the RDS file
  rds_object <- readRDS(file_path)
  
  # Create a description
  description <- list(
    "File Name" = basename(file_path),
    "Object Class" = class(rds_object),
    "Object Length" = length(rds_object),
    "Object Dimensions" = ifelse(is.matrix(rds_object) || is.data.frame(rds_object), 
                                  paste(dim(rds_object), collapse = " x "), 
                                  "N/A"),
    "Object Summary" = capture.output(summary(rds_object)),
    "Object Structure" = capture.output(str(rds_object, max.level = 1)),
    "First Few Elements" = if (is.atomic(rds_object) || is.list(rds_object)) {
      utils::head(rds_object, n = 3)
    } else {
      "Not applicable for this type."
    }
  )
  
  # Print the description
  cat("========== RDS File Description ==========\n")
  cat(paste("File Path:", file_path), "\n\n")
  cat("Object Class:", description$`Object Class`, "\n")
  cat("Object Length:", description$`Object Length`, "\n")
  cat("Object Dimensions:", description$`Object Dimensions`, "\n\n")
  cat("Object Summary:\n", paste(description$`Object Summary`, collapse = "\n"), "\n\n")
  cat("Object Structure:\n", paste(description$`Object Structure`, collapse = "\n"), "\n\n")
  
  # Print First Few Elements (if applicable)
  if (!is.character(description$`First Few Elements`)) {
    cat("First Few Elements:\n")
    print(description$`First Few Elements`)
  } else {
    cat("First Few Elements: ", description$`First Few Elements`, "\n")
  }
  
  return(invisible(description)) # Return the full description for further use
}
# List of RDS files
rds_files <- list.files(path = run.id, pattern = "\\.RDS$", full.names = TRUE)

# Describe each file
rds_descriptions <- lapply(rds_files, describe_rds)
