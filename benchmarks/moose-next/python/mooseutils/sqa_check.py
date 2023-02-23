#!/usr/bin/env python2
#* This file is part of the MOOSE framework
#* https://www.mooseframework.org
#*
#* All rights reserved, see COPYRIGHT for full restrictions
#* https://github.com/idaholab/moose/blob/master/COPYRIGHT
#*
#* Licensed under LGPL 2.1, please see LICENSE for details
#* https://www.gnu.org/licenses/lgpl-2.1.html

import os
import collections
import subprocess
from hit_load import hit_load
from mooseutils import git_root_dir, colorText

def check_requirement(filename):
    """Check spec file for requirement documentation."""

    messages = []
    root = hit_load(filename)
    design = root.children[0].get('design', None)
    issues = root.children[0].get('issues', None)
    for child in root.children[0]:
        if 'requirement' not in child:
            messages.append("    'requirement' parameter is missing in '{}' block.".format(child.name))

        if child.get('design', design) is None:
            messages.append("    'design' parameter is missing in '{}' block.".format(child.name))

        if child.get('issues', issues) is None:
            messages.append("    'issues' parameter is missing in '{}' block.".format(child.name))

    if messages:
        print 'ERROR in {}'.format(filename)
        print '\n'.join(messages) + '\n'
        return 1
    return 0

def sqa_check(working_dir=os.getcwd(), remote='origin', branch='devel', specs=['tests'], skip=[]):
    """Check that test specifications that were modified include requirements."""

    # Fetch
    cmd = ['git', 'fetch', remote]
    subprocess.call(cmd)

    # Root directory of repository
    root = git_root_dir(working_dir)

    # Check requirements on changed tests specs
    count = 0
    cmd = ['git', 'merge-base', '{}/{}'.format(remote, branch), 'HEAD']
    sha = subprocess.check_output(cmd).strip()
    cmd = ['git', 'diff', sha, '--name-only']
    for filename in subprocess.check_output(cmd).split('\n'):
        if os.path.isfile(filename) and (os.path.basename(filename) in specs) and \
           not any(s in filename for s in skip):
            count += check_requirement(os.path.join(root, filename))

    return count

def sqa_check_requirement_duplicates(working_dir=os.getcwd(), specs=['tests'], skip=[]):
    """Check that no duplicate requirements exist."""

    requirements = collections.defaultdict(list)
    for root, dirs, files in os.walk(working_dir):
        for fname in files:
            filename = os.path.join(root, fname)
            if fname in specs and not any(s in filename for s in skip):
                node = hit_load(filename)
                for child in node.children[0]:
                    req = child.get('requirement', None)
                    if req is not None:
                        requirements[req.strip()].append((filename, child.fullpath, child.line('requirement')))

    count = 0
    for key, value in requirements.iteritems():
        if len(value) > 1:
            if count == 0:
                print colorText('Duplicate Requirements Found:\n', 'YELLOW')
            count += 1
            if len(key) > 80:
                print colorText('{}...'.format(key[:80]), 'YELLOW')
            for filename, path, line in value:
                print '    {}:{}'.format(filename, line)

    return count
