# Usage

- [Usage](#usage)
  - [Search for recipes](#search-for-recipes)
  - [Build a recipe](#build-a-recipe)
  - [Create your own recipes](#create-your-own-recipes)
  - [Create your own cookbook](#create-your-own-cookbook)
    - [To use a local cookbook directory](#to-use-a-local-cookbook-directory)
    - [To use a private cookbook repository](#to-use-a-private-cookbook-repository)

## Search for recipes

Download recipes from public sources:

> `mussels update`

or:

> `msl update`

View recipes available for your current platform:

> `msl list`
>
> `msl list -V` (verbose)

Many Mussels commands may be shortened to save keystrokes. For example, the following are all equivalent:

> `msl list`
>
> `msl lis`
>
> `msl li`
>
> `msl l`

View recipes for available for _all_ platforms:

> `msl list -a`
>
> `msl list -a -V`

Show details about a specific recipe:

> `msl show openssl`
>
> `msl show openssl -V` (verbose)

## Build a recipe

Perform a dry-run to view order in which dependency graph will be build a specific recipe:

> `msl build openssl -d`

Build a specific version of a recipe from a specific cookbook:

> `msl build openssl -v 1.1.0j -c clamav`

## Create your own recipes

A recipe is just a YAML file containing metadata about where to find, and how to build, a specific version of a given project.  The easiest way to create your own recipe is to copy an existing recipe.

Use the `list` command to find a recipe you would like to use as a starting point:

> `msl list -a -V`

Once you've chosen a recipe, copy it to your current working directory with the `clone` command. For example:

> `msl clone nghttp2`
>
> `ls -la`

_Tip_: If the recipe requires one or more patch-sets to build, the corresponding patch directories will also be copied to your current working directory.

Now rename the cloned recipe to whatever you like and start making changes! So long as you keep the `.yaml` extension, Mussels will still recognize it.

_Tip_: When testing your recipes, the recipes must be in, or in a subdirectory of, your current working directory in order for Mussels to find them.  Use `msl list -a -V` to display all current recipes.  Recipes found in the current working directory will show up as being provided by the "local" cookbook.  Use `msl show <recipe_name> -V` to view more information about a specific recipe.

## Create your own cookbook

Simply put, a cookbook is a Git repository that contains Mussels recipe files and/or Mussels tool files.  The structure of the cookbook is up to the project owners as is the naming convention for recipe and tool files. To identify recipes and tools, Mussels will search every YAML file in the repository for files containing `mussels_version` key.

Cookbooks are a way for users to curate recipes to build their project without relying on recipes provided by others where changes may inadvertantly break their build. As cookbooks are privately owned, their owners are free to copyright and license the recipe and tool definitions within as they see fit.

The Mussels project maintains [an index](mussels/bookshelf.py) of cookbooks provided by third-parties. Cookbook authors are encouraged to add their cookbook to the index by submitting a pull-request to the Mussels project. However, we ask that each cookbook's license must be compatible with the Apache v2.0 license used by Mussels in order to be included in the index.

You don't need to add your cookbook to the public index in order to use it.

### To use a local cookbook directory

Simply `cd` to your cookbook directory and execute `mussels` commands in that directory for it to detect the "local" cookbook.

### To use a private cookbook repository

  Run:

  > `msl cookbook add private <Git URL>`

  This will add the Git URL for your cookbook to your global Mussels config.  Mussels will record your cookbook in the index on your local machine.

  In the above example we used the name `private` but you're free to choose any name for your cookbook.

  Then run:

  > `msl update`

  Mussels will clone the repository in your `~/.mussels` directory and the recipes will be available for use.

  Now you should be able to the recipes and tools provided by your cookbook with:

  > `msl cook show private -V`

  and reference your cookbook's recipes with:

  > `msl show my_recipe -c private`
  >
  > `msl build my_recipe -c private -d`
