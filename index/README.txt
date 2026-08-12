UIL PREP REDESIGN
=================

Open main.html to start the site.

Included files
--------------
main.html     Home and primary entry point
info.html     Competition path, alignments, calendar, and support
event.html    Searchable and grade-filterable event catalog
survey.html   Accessible event-fit assessment
styles.css    Shared UIL brand and responsive design system
app.js        Shared navigation, reveal, event filter, and alignment behavior
survey.js     Assessment questions, navigation, scoring, and results
UIL-logo.jpg  Supplied UIL logo used across the site and as the browser icon

Event homepages
---------------
events/calcapps/calc.html          Calculator Applications
events/chess/chess.html            Chess Puzzle
events/impromptu/imprompt.html     Impromptu Speaking
events/mathematics/math.html       Mathematics
events/numbersense/numsense.html   Number Sense
events/OO/oratory.html             Modern Oratory
events/oralreading/oral.html       Oral Reading
events/science/science.html        Science
events/socialStudies/social.html   Social Studies
events/spelling/spelling.html      Spelling

Notes
-----
- The site uses no external font or animation libraries.
- Motion uses lightweight native CSS/JavaScript and honors reduced-motion settings.
- Each event homepage includes a resource dock designed for future lessons,
  practice tests, and tools. Unfinished resources are visibly marked "Future"
  and keep their intended filename in a data-future-href attribute. After a
  resource page is built, replace its span with an anchor using that filename.
- The calendar requires an internet connection.
- info.html preserves the existing optional ../alignments/links.js integration.
  When that file is unavailable, conference buttons safely open the official
  UIL Academic Alignments page.
- This is an independent preparation resource, not an official UIL website.
