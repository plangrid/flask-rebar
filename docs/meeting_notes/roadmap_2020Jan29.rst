V2.0 Roadmap Call 2020-Jan-29
=============================

Agenda and Notes
----------------

* Plans for our next major version release, v2.0

  * Removing support for old versions of Python (notably 2.x)

  * PEP561 compliance (deferred)

  * Adding support for (or moving to?) Marshmallow 3

  * Expose swagger deprecated parameter

  * Hidden APIs

  * Marshmallow

    * Should we remove v2 completely?

    * We NEED to support 3. No reason to not support 2 as well.  Removing 2.0 could prevent a lot of projects from upgrading rebar

  * We came to agreement over what should and shouldn’t be in v2.0

    * All v2.0 issues here: https://github.com/plangrid/flask-rebar/issues?q=is%3Aissue+is%3Aopen+label%3Av2.0

    * Items considered general future nice-to-have but can wait until after 2.0 release are tagged v2.1

    * Other "fix as needed/available" Issues remain with no v2.x tag (Editor's note - unless anyone has a pressing need for something in one of those I would guess they'll end up being more 2.2+ unless they just happen to get worked into ongoing changes naturally)

* Go over open pull requests

* Went over a few issues

  * Issue around us masking Flask responses

    * What if we want to send 304s and other responses that don’t return the resource?

  * Concerns around “Code first” vs “YAML first”

    * For people who would have to write XML etc., Using YAML is nice, but Python is much better at doing this. Python over YAML.

    * Flask-rebar is traditionally “Code-first”. We get the OpenAPI spec for free. However as time goes on we want more configurable control over the spec.

      * Issue #136 is an example of this: https://github.com/plangrid/flask-rebar/issues/136

      * Can we supply a backdoor that allows you to have more fine grained control of specs if you so choose to?

    * Using extensions of OpenAPI is hard right now in flask-rebar because it has to be code supported first.

    * This is hard since we want rebar to mash OpenAPI, Marshmallow and Flask all together.

    * Flask supports cookie authentication now, but rebar doesn’t

  * https://github.com/plangrid/flask-rebar/issues/131 lots of thread local vars.. would be nice to use objects and have them type annotated nicely.. maybe a nicer way to wrap flask api to do this more cleanly?

  * https://github.com/plangrid/flask-rebar/issues/91 - maybe overkill.. not a lot of demand for full on content negotiation, more just including support for other serialization format.. some question on how content negotiation fits in to openapi  

  * https://github.com/plangrid/flask-rebar/issues/12 - Yet another example of an issue around building in finer-grained control over OpenAPI output

    * QOTD: "Just, please don't make me write yaml in docstrings" :D 

* Rough timeline to target v2.0 release?

  * Do we want to schedule a monthly review?

    * Decided to keep meetings ad hoc for now, coordinate more via Discord (see below)

  * Review contribution process, pain points etc.

    * Write-access controls are restrictive - not sure if/what we can do about this but should look into making this as open as possible without causing chaos (or violating any company policies).  Would be nice if people could self-assign issues, create sub-projects, etc

  * We didn't really land on any kind of timeline yet - good fodder for ongoing discussion as we increase our capability for live collaboration vs communications via GitHub Issues ;)

* Discussion around wants/needs – balancing ACS requirements (which tend not to drive Flask-Rebar improvements unless there’s a pressing business need) with the needs of the OSS community (keeping Flask-Rebar useful, current, and relevant)

  * We should add labels for documentation issues/PRs. So we did :)

  * Documentation is rough right now.

    * FastAPI is a great example of what we should be at.

  * Middleware capabilities? Can we just use WSGI for this?

    * Seems like yes?

* Should we create some channel for this group and the software in general?

  * Flask has a discord. Let’s create a channel in it! (So we did: Join `Pallets Project Discord <https://discord.gg/t6rrQZH>`_ and find us in the flask-rebar channel!)

* Should we start using github projects?

  * Would help with prioritizing issues and figuring out how to move forward

* We should try and arrange meetups at upcoming conferences (Flask conference?)
