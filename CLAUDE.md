# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Interactions

- Do not make up data
- Talk to me directly
- Be concise and to the point
- Be critical of my requests and your own work

## Project Overview

**grep-dap** is a package for inferring the contents of an OPeNDAP server.

## Primary context

I’m interested in the potential use of GenAI to help address the loose metadata constraints associated with OPeNDAP. Some background: The OPeNDAP DAP (data access protocol) was designed with a rigid syntactic metadata structure and a virtually free semantic metadata structure. The syntactic metadata defines the structure of the data. One way to think about this is that it is the metadata that is needed figure out how to plot the data. The semantic metadata tells you about the meaning and provenance of the data, what you would, for example, need to label plots of the data. OPeNDAP is a client-server protocol. 

The idea is that a user makes a request, from their application, for a subset of a dataset on a remote verser. The form of the request is rigidly defined by the DAP. On the server side there is a translator, which maps the data from the structure in which it is stored to the structure of the DAP. The server also extracts the specified subset of the data from the archive. The extracted and reformatted data are compressed and sent to the client side. On the client side they are decompressed and converter to the data model of the client. The user can request what metadata there is as well. The reason for the loose constraints on the metadata is that when we built the system we were concerned that if a rigid structure for the metadata was specified many potential providers would simply not serve their data.

The result is that there are many OPeNDAP servers but, not surprisingly, the metadata associated with these data sets varies from nonexistent to very complete; i.e., a weakness and a strength of OPeNDAP is the lack of constraints on the metadata. Even for a dataset with no semantic metadata there is often information associated with the data that might help in sorting out of the semantic information. For example, there is information in the names of files and folders, the syntactic metadata of the data says something about its content—an 8 dimensional array is not likely to be a collection of photographs of paintings—and there is information in the structure, the relationship between data elements in, for example, a 2d array.

I have been involved in work in which we have used contrastive learning to characterize SST fields. Given another archive of 2d fields, I could apply the model we developed to the new data to see what the probability is that it is SST data. You get the idea.  One of the beauties of OPeNDAP is that I can easily sample data from archives if I know the server address. Given that some archives are very well defined I can compare, in a statistical sense, samples from these with samples from the new archive…

# OPeNDAP

Information about OPeNDAP servers may be found here:

https://www.earthdata.nasa.gov/engage/open-data-services-software/earthdata-developer-portal/opendap

# Code guidelines

- Reuse existing code when possible

## Python

Adhere to following:

- Generate methods when possible, not classes
- Include inline comments
- Use matplotlib for plotting

If you run Python code, use the "ocean14" conda environment.

To interact with an OPeNDAP server, you may wish to use the pydap package.  Its documentation is located here https://pydap.github.io/pydap/en/intro.html

# Overleaf

Place any Latex files in /home/xavier/Projects/overleaf/grepdap/

You may push to git as you work.  The access token is in my .bashrc profile with the name OVERLEAF.


