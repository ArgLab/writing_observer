'''
Roles defined for the system. We explicitly do not want the complexity
of ACLs, roles, groups, etc. We plan four levels, including later a
school/district-level one.

We create the enum for roles like this to make everything
a string and thus, it is all json serializable. Starting in
Python 3.11, there is an easier way to do this.
`ROLES = enum.StrEnum("ROLES", names=('STUDENT', 'TEACHER', 'ADMIN'))`
'''
import collections
import os
import shutil

import learning_observer.paths as paths
import learning_observer.prestartup

class ROLES:
    pass
possible_roles = ['STUDENT', 'TEACHER', 'ADMIN']
[setattr(ROLES, role, role) for role in possible_roles]

'''
TODO we should include other methods of determining
where to pull the list of users from. In the future we want
to allow text-based and database backends. We should support
multiple methods of retrieving this information at once.
'''
USER_FILES = collections.OrderedDict({
    ROLES.ADMIN: 'admins.yaml',
    ROLES.TEACHER: 'teachers.yaml',
})


@learning_observer.prestartup.register_startup_check
def validate_user_lists():
    '''
    Validate the role list files. These are YAML files that contains
    a list of users authorized for each role to use the Learning Observer.
    '''
    for k in USER_FILES.keys():
        if not os.path.exists(paths.data(USER_FILES[k])):
            shutil.copyfile(
                paths.data(f"{USER_FILES[k]}.template"),
                paths.data(USER_FILES[k])
            )
            raise learning_observer.prestartup.StartupCheck(
                f"Created a blank {k} file: {paths.data(USER_FILES[k])}\n"
                f"Populate it with {k} accounts."
            )
