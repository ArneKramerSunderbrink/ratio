Readme for future developers
======
This tool is not actively developed anymore (since August 2021). The purpose of this document is to provide an entry point for potential future development.

A quick word on the generality of the tool
-------
First of all, I initially assumed that I was supposed to develop a general tool that could work with different ontologies: You install a general version of the tool on your server
and then upload your own ontology and other configuration files. The dummy data contains the configuration files that are used for our special use case.
However, later that turned out to be irrelevant because the tool would only be used for one purpose with one ontology and the strict distinction between the general tool and the
configuration for the specific use case were not sustained if that would mean significantly more effort.
In particular, the script deploy.sh installs both the general tool and our specific configuration and the template `overview_table.html` is made specifically for our ontology and would not work
with any other because I haven't found a way that users could specify different overview tables without allowing them to upload arbitrary code that would be executed on the server.
Further, the tool was never tested with any other configuration and there is no documentation as to what properties an ontology must have to work with the general tool.

Nevertheless, most small changes to the tool (e.g. adding the option to give the DOI of a publication) can be achieved by simply changing the ontology, without touching the actual code.

Ontology
------
The RATIO tool manages an RDF database according to an ontology. Data is added to subgraphs of the complete knowledge graph. In our application, subgraphs contained information about a 
specific clinical trial.

The CTRO ontology used by us can be found in `ontology_original.ttl`. To work as a configuration for the tool, certain
information has to be added. The editor of the tool is a tree where the nodes are entities (owl:NamedIndividual) that have fields (owl:ObjectProperty or owl:DatatypeProperty) 
with values (owl:NamedIndividual or literals). owl:NamedIndividual values can either be from a predefined list (e.g. ctro:hasGender), 
or defined and described elsewhere in the tool (e.g. ctro:hasArmOut), or defined and described directly (e.g. ctro:hasArm).
The last option corresponds to a branching of the tree and is marked by a triple (ctro:hasArm ratio:described "true"^^xsd:boolean) that has to be added to the original ontology.

Before describing the additional information, here is the 'normal' ontology elements that are used by the ontology. Hopefully it is somewhat intuitive how it is used, I will not explain it here.
1. Every owl:ObjectProperty and owl:DatatypeProperty has to have a rdfs:domain, a rdfs:range, and a rdfs:label.
   Additional information (displayed when hovering over the corresponding element in the tool) can be provided via a rdfs:comment.
   They can also be specified to be functional (allow not more than one value, zero values is ok) via owl:FunctionalProperty.
2. rdfs:domain and rdfs:range of a property have to be described as owl:Class and every class has to be a rdfs:label and optionally a rdfs:comment.
   Classes can be structured via rdfs:subClassOf.
   Restrictions like owl:equivalentClass are ignored.
3. Predefined individuals that can be values of object properties that are not described are defined as owl:NamedIndividual with rdfs:label and optionally rdfs:comment.

Here is a list of all information you can add to a property in the configuration ontology:
1. _ratio:described_: 
   Marks an owl:ObjectProperty as branching into other described entities. 
   Example: ctro:hasArm ratio:described "true"^^xsd:boolean
   Default: False.
2. _ratio:deletable_: 
   Marks an owl:ObjectProperty as being 'essential'. Essential objects cannot be deleted or added or renamed. Therefore, they have to already exist in the initial graph 
   (see `new_subgraph.ratio` on how to specify the initial graph). Only described properties can be essential. 
   Example: ctro:hasPopulation ratio:deletable "false"^^xsd:boolean 
   Default: True.
3. _ratio:order_: 
   Since an RDF graph is not ordered, we need to specify the order in which the fields are displayed in the tool. 
   Example: ctro:hasPopulation ratio:order "4"^^xsd:positiveInteger
   Default: 0, but This should not be used. Values (1,2,...) should be explicitly specified for all properties to ensure consistency of the display.
4. _ratio:width_:
   For properties that are not described, the width of the corresponding input field can be specified in percent.
   Example: ctro:hasGender ratio:width "25"^^xsd:positiveInteger
   Default: 50.

Further, one can add subheadings to the display that are not part of the knowledge but merely there to structure the fields of a described entity when necessary. 
They are modelled as 'pseudo properties'.Example:
```
ctro:hasStatisticalMeasure rdf:type ratio:Subheading ;
                           ratio:order "10"^^xsd:positiveInteger ;
                           rdfs:domain ctro:Outcome ;
                           rdfs:label "Statistical measurements:" .
```

Finally, one has to specify the base of the URIs the tool will create for entities created by the user via `ratio:Configuration ratio:hasBase "http://www.semanticweb.org/root/ontologies/2018/6/ctro#"`.
So in this case, when a user adds a second arm to a clinical trial with index 7, the tool will give it the URI `ctro:Arm_7_2`.



Remote access to the webtentacle server
------
Currently, the tool is running on the webtentacle server of the technical faculty of the University Bielefeld. Here is how I accessed it remotely:
1. Access techfak shell via `ssh techfakusername@shell.techfak.de`. See [this guide](https://techfak.net/dienste/remote/shell) on how to set this up.
2. From there, access webtentacle via `ssh webtentacleusername@webtentacle1.techfak.uni-bielefeld.de`. Ask an admin to get you a username and a password.
3. I stored the data for the tool at `~/ratio`.
4. I found [this](https://bashupload.com/) to be the most convenient way to get files to and from the server.

Update workflow
------
Here is what I did when I updated the tool:

1. Make and test changes locally.
2. 1. If the tool is running on the server: In the admin interface, set the admin message to something like
   "The tool will be updated today (01.02.2021) from 20:00 to 00:00. Changes made in that time are not persisted in the database" (if people are actively using it, else skip the admin message). 
   At the specified time download the backup from the admin interface.
   2. If the tool is not running and cannot be started (maybe because the version on the server is broken), access the server, go to `~/ratio/venv/var/ratio-instance` 
      and download the database `ratio.sqlite`.
3. Replace `dummy_db.sqlite` with the database just downloaded from the server, do `flask db-init` and `flask db-add-dummy`, test again with the new database.
   If there is an error in the database itself (maybe the tool accidentally stored an `owl:NamedIndividual` without a `ctro` type or something like that, 
   causing a crash when trying to display the subgraph in the tool), use your favourite SQL tool (e.g. SQLite directly or python with `sqlite3`) to find and fix it.
4. Stop the tool on the server with `pkill gunicorn` and delete everything from the `~/ratio` folder.
5. Install and run the updated tool on the server. See _Deploy with Gunicorn_ in `README.md`.

Loose ends
-------
Here are some todos I would look into if I would continue work on the system (apart from the todos directly in the code):
1. _Search.py_: The filter of the search page works basically like the Knowledge editor, code from `knowledge_model.py` was simply copied and modified.
   It would be cleaner if `Filter` and `FilterField` would inherit `Entity` and `Field` from `knowledge_model.py` to share as much code as possible.
2. _Clean the Database_: Literal values are deleted by making the corresponding fields empty, when reloading the page they are removed from the view.
   However, for some reason I don't remember unfortunately (something about having a list of values in a field and deleting something from the middle
   or something like that) they are not deleted from the database. This yields to empty values accumulating in the database over time. This values could be cleaned up
   everytime a user reloads the editor for example (I initially thought multiple people should be able to work on a subgraph and therefore this would not be a viable solutionb
   but this turned out to be false later). Or maybe there is even a better solution for the problem in the first place, if I'd
   only remember what it was...
3. _Tests_: I added tests in the early stages of development, but in a phase of hasty development I gave up on updating them. The test infrastructure is still there but none of them work anymore.
4. _Admin account_: My intention with the admin interface was to avoid the update workflow described above as much as possible and allow as much bug fixing as possible in the admin interface
   while the tool is running.
   1. Clear the whole database (like the init-db command).
   2. Upload a new ontology.
   3. Download and upload the SQLite rows of single specific subgraph.
   4. Replace all occurences of the URI A with the URI B in the knowledgebase.
5. _Messages_: The frontend for the little messages at the bottom of the screen is really messy. It would be great to have a uniform way of displaying arbitrary messages that works the same
   way for every page. This could be achieved by storing all messages in the global attribute flask.g and making a uniform message macro and put the same loop that displays all
   messages on every page template and write code to handle user interactions with the messages in `base.js`.
