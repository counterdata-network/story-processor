# Query Syntax Guide: Mastering Search Techniques

When conducting advanced searches, the structure of your query can make a significant difference in the relevance and quality of your results. This guide will walk you through the process of building precise queries, followed by searching techniques and examples of queries as well as what they are searching for.

## Step-by-Step Instructions for Assembling a Query

### 1. Identify Key Search Terms

The first step in creating a query is identifying the essential keywords and phrases that will lead to the desired search results. This includes specific terms related to the topic you're researching.

**Example:**
You want to find cases involving unsolved murders of Indigenous women using genetic genealogy.

Key terms: `murder`, `woman`, `Indigenous`, `genetic genealogy`

*Note:* Our searches are case-insensitive

### 2. Use Boolean Operators

Boolean operators (AND, OR, NOT) allow you to refine your search by combining or excluding terms.

* **AND**: Returns results that contain all specified terms
* **OR**: Expands the search to include results containing any of the terms listed
* **NOT**: Excludes specific terms

**Example:**
You want results that include murder-related terms and genetic genealogy, but also include variations on gender and identity:

```
(murder OR homicide OR femicide OR feminicide) AND (woman OR girl OR Indigenous) AND genetic genealogy
```

You want to match any variety of ways the incident is covered: `murder OR homicide OR femicide OR feminicide`

And you want to match different ways the victim or survivor is identified: `woman OR girl OR Indigenous`

### 3. Group Terms with Parentheses

Parentheses help group terms and clarify the order of operations in complex queries. In queries, parentheses override the default order of operations, meaning that any expression within parentheses will be evaluated first, before any other operations outside of the parentheses are performed.

**Example:**
You want to search for various violent acts alongside gender identities. Group the terms to maintain clarity:

```
(murder OR homicide OR femicide) AND (woman OR girl OR Indigenous)
```
### 4. Add Phrase Searches

To find exact phrases, use quotation marks around the phrase you're looking for.

**Example:**
You want results with the specific phrase "genetic genealogy":

```
"genetic genealogy"
```
If the quotations were not present, the system would interpet it as `genetic AND geneaology`.

### 5. Include Wildcards

Use wildcards (`*`) to capture variations of a word. The `*` wildcard represents any number of characters.

**Example:**
Searching for variations of woman and girl, such as plural cases, you can use `wom\*n` or `girl*` to include results like "women" or "girls":

```
(wom*n OR girl*)
```
Note: But be careful, because `wom\*` can also match "wombat".

### 6. Combine and Refine

Now, combine all elements to create a more targeted query that captures all relevant terms and excludes irrelevant information.

**Final Example Query:**
```
((murder OR homicide OR femicide OR feminicide) AND (woman OR girl OR Indigenous) AND "genetic genealogy")
```


## Query Syntax Sorted by Prevalence

### 1. **AND/OR Capitalization**
- Boolean operators like AND and OR must be capitalized. Group ORs and ANDs for clarity.
- **Example:**
    - `(church OR faith) AND (lesbian OR gay OR LGBTQ)`

### 2. **Searching for an Exact Phrase**
- Searches for an exact match of the phrase.
- **Example:**
    - Use double quotes to match an exact phrase like `"unhoused person"`

### 3. **Default Search**
- When no Boolean operator is used, the default assumption is AND.
- **Example:**
    - `monkey banana` is equivalent to `monkey AND banana`

### 4. **Negation**
- Use `NOT` or `-` to exclude terms from your search
- **Example:**
    - `Gaza NOT Hamas` will return results about Gaza but exclude any result mentioning Hamas.
      
### 5. **Word Stems** / **Multiple Character Wildcard**
- Match multiple conjugations or variations of a word by using a wildcard (`*`) after the root word.
- **Examples:**
    - `"learn*"` will match "learn", "learner", "learning", etc.
    - `wom*n` or `wom*` works to match things like `women` or `woman`.

### 6. **Single Character Wildcard**
- Match terms where a single character can vary in a specific position using `?`.
- **Example:**
    - `"wom?n"` works to match "woman" or "women".

### 7. **Proximity Search**
- Use a tilde with a number after it to find words that appear within a certain number of words from each other.
- **Example:**
    - `"woman killed"~10` will return results where "woman" and "killed" are within 10 words of each other.

### 8. **Fuzzy Queries**
- The tilde (`~`) after a word allows for slight misspellings or variations.
- **Example:**
    - `"Biden~"` will match any slight misspellings like "Bidan" or "Bidden".

### 10. **Search Titles Only**
- Our system automatically searches body texts and article titles
- We do not have the functionality to specify searching titles only

### 10. **Hyphens**
- Wrap hyphenated phrases in double quotes to ensure the entire phrase is treated as one unit.
- **Example:**
    - `"two-spirit"` needs to be in double quotes.

### 11. **Language Filter**
- Filter results based on language using `"language:code (ISO 639-1)"`.
- **Example:**
    - `Biden AND language:en` returns results in English, while `Biden AND language:es` returns results in Spanish.
Wikipedia has a [reference list of language codes](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes).

### 13. **Regular Expressions**
- Regular expressions are not supported in most search engines like Media Cloud or Wayback Machine.


## Example Queries and What They Are Searching For

### 1. Searching for Unsolved Murder Cases Involving Women or Marginalized Groups

**Query Objective:**
This query looks for articles or reports related to unsolved or cold cases involving murders of women, girls, transgender individuals, nonbinary people, Indigenous people, or other marginalized identities. It also seeks cases where genetic genealogy might have been used to solve the crime.

**Final Query:**
```
((murder OR homicide OR femicide OR feminicide OR murdered OR dead OR death OR killed OR shot OR stabbed OR struck OR strangled OR "life-less") AND (woman OR girl OR transgender OR trans OR nonbinary OR non-binary OR Indigenous OR "Native American" OR two-spirit OR "two-spirit" OR "a young woman" OR "a teenage girl" OR "a girl" OR "body of a woman" OR prostitute OR "sex worker") AND ("cold case" OR "genetic genealogy"))
```
**Groupings:**
- First group captures various ways of describing death or violent acts
- Second group identifies potential victims using inclusive terminology
- Third group narrows results to cold cases or those using genetic genealogy

### 2. Searching for Violent Deaths of Black and Indigenous Women and Gender-Diverse People

**Query Objective:**
This query is designed to find reports involving violent deaths or unnatural deaths of women, transgender people, nonbinary individuals, with a specific focus on Black and Indigenous victims. The query combines racial and gender identities with various forms of death and violence to capture intersectional experiences.

**Final Query:**
```
((murder* OR homicide* OR femicide OR feminicide OR murdered OR dead OR death* OR 
killed OR murdered OR shot OR stabbed OR struck OR strangled OR "life-less") 
AND 
(wom*n OR girl* OR transgender OR trans OR nonbinary OR "non-binary" OR 
"African American" OR "African-American" OR "African descent" OR Black OR 
Indigenous OR "Native American" OR "two-spirit" OR "two spirit" OR prostitute OR 
"sex worker"))
```
**Groupings:**
- First group uses wildcards on key terms (`death*`, `murder*`) to capture variations of violent death descriptions such as death/deaths and murder/murders
- Second group combines gender identity terms with racial identity terms, including multiple formats for Black and Indigenous identities
- Terms capture both formal (African American) and commonly used (Black) racial identity descriptors
- Includes specific cultural identity terms like `two-spirit` that intersect with both gender and Indigenous identity
