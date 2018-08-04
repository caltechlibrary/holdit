'''
exceptions.py: exceptions defined by Holdit
'''

class UserCancelled(Exception):
    '''The user elected to cancel/quit the program.'''
    pass

class ServiceFailure(Exception):
    '''Unrecoverable problem involving network services.'''
    pass

class InternalError(Exception):
    '''Unrecoverable problem involving Holdit itself.'''
    pass
