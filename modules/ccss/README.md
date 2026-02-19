# Common Core State Standards for Python

This is a small package which allows the use of Common Core State Standards from Python.

     import ccss
     ccss.standards
     ccss.standards.math()
     ccss.standards.math().grade(5)
     ccss.standards.ela().subdomain('CCRA')
     ccss.standards.ela().subdomain('LF').grade([5,6])

These will all return dictionary-like objects mapping CCSS tags to their text. Queries can be changed in arbitrary order.

It's possible to see options available. For example:

     ccss.standards.grades()
     ccss.standards.subdomains()
     ccss.standards.subdomain('CCRA').grades()

You should be mindful of [licensing issues with Common Core](ccss_public_license). This code is open-source. The standards are not.

The text is also scraped, and there are occasional bugs. We are missing a few tags, and a few have partial text. Feel free to submit a PR to fix it!

This package is in development. If you use it in your project, we recommend pinning versions, as the API may change (but it's very usable in the current version, and we don't anticipate specific reasons to upgrade just because a newer version exists).