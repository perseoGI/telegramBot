CREATE_CATEGORY, DELETE_CATEGORY, EDIT_CATEGORY = range(1, 4)

# First '0' to null. callback cannot take '0' value because it has to be a string ('0' is a null)
ACTION_COMPLETE, ACTION_UNCOMPLETE, ACTION_POSTPONE, ACTION_EDIT, ACTION_BACK, ACTION_FINISH, ACTION_NEXT, ACTION_NONE = range(1,9)
