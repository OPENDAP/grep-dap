# Test case with URI OPeNDAP server

Read the CLAUDE.md file to gain context about the project.

# Primary objective

Perform an exploratory analysis of data in a URI OPeNDAP server.  Use this URL to access data at URI: https://sst-aqua.gso.uri.edu/opendap/

# Additional context

This document contains information about OPeNDAP and pydap:
/home/xavier/Projects/overleaf/grepdap/opendap_readme.tex

# Overleaf

Make a log of any of your commands and of your thoughts in a file named test_case_uri_log.tex in the /home/xavier/Projects/overleaf/grepdap/ directory.  Be sure to add a timestamp any time (including time of day) that you add a new section to the log.

Generate a standlone LateX file named uri_test_case.tex in the /home/xavier/Projects/overleaf/grepdap/ directory that describes your findings.

# Scripts

If you will execute a series of Python commands, save them in a file named <script_name>.py in the /home/xavier/Projects/grepdap/scripts/ directory.


# Prompts

1. Read this document.  Explore the contents of the URI OPeNDAP server.  Describe the data and the metadata.  Describe the data within the server and explain your reasoning.  Be mindful of the overall project that we are working on.  Spend up to 1 hour on this task.  

2. This is an excellent start.  Reread this document. Explore further the gradients_by_period dataset.   See if you can better infer the semantic metadata for this dataset, both global and for each variable.  Generate guesses that are COARDS compliant and provide your explanations for each.  Update the log file and the uri_test_case.tex file accordingly.  

3. Thanks.  Can you configure the COARDS per-variable attributes in Section 6.3.3 of uri_test_case.tex to follow what was done for the coordinates?  Also, Table 6 has overlapping text between columns.  Please fix that too.

4. Given the semantic metatadat that you have generated for the gradients_by_period dataset, can you provide a description of the data and how it was generated?  Add to the uri_test_case.tex file accordingly.  If you need to do any additional analysis, please do so and add to the log file and the uri_test_case.tex file accordingly.

5. Please estimate the spatial range over which the gradients were calculated.  Add your estimate and reasoning to the document.

6. NASA's primary search engine for datasets is EarthData Search.  Please generate an entry for EarthData Search that describes the gradients_by_period dataset.  Generate a new file for this that conforms to the EarthData Search format.