'''
Writing Observer Portfolio Diff

A writing observer module that shows the difference between the works of a student
'''

# Name for the module
NAME = 'Writing Observer Portfolio Diff'


'''
The Course Dashboards are used to populate the modules
on the home screen.

Note the icon uses Font Awesome v5
'''
COURSE_DASHBOARDS = [{
    'name': NAME,
    'url': "/wo_portfolio_diff/portfolio_diff/",
    "icon": {
        "type": "fas",
        "icon": "fa-play-circle"
    }
}]

'''
Built NextJS pages we want to serve.
'''
NEXTJS_PAGES = [
    {'path': 'portfolio_diff/'}
]