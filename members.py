from member import Member


class Members:

    def __init__(self, db):
        self.members = []
        self.db = db
        self._getCurrentMembers()

    def AddPrimaryMember(self, IP):
        member = Member(_id=0, IP=IP, priority=1)
        self.members.append(member)

    def AddMember(self, IP):
        try:
            print('Members.AddMember: ATTEMPTING TO ADD {}'.format(IP))
            memberIDs = []
            newID = 0
            for member in self.members:
                memberIDs.append(member._id)
            for i in range(0, 255):
                if i not in memberIDs:
                    newID = i
            newMember = Member(_id=newID, IP=IP, priority=0.5)
            state = newMember.CheckIfAlive()
            if state == True:
                self.members.append(newMember)
                print('Members.AddMember: ADD {}'.format(IP))
                return True
            else:
                print('Members.AddMember: FAILED TO ADD {}'.format(IP))
                return False
        except Exception as error:
            print('Members.AddMember: ERROR\t{}'.format(error))

    def RemoveMember(self, IP):
        try:
            print('Members.RemoveMember: ATTEMPTING TO REMOVE {}'.format(IP))
            for member in self.members:
                if member.IP == IP:
                    self.members.remove(member)
                    print('Members.RemoveMember: REMOVED {}'.format(IP))
                    return True
            print('Members.RemoveMember: FAILED TO REMOVE {}'.format(IP))
            return False
        except Exception as error:
            print('Members.RemoveMember: ERROR\t{}'.format(error))
            return False

    def Serialize(self):
        members = []
        for member in self.members:
            members.append(member.Serialize())
        return members

    def _getCurrentMembers(self):
        try:
            conf = self.db.admin.command('replSetGetConfig', 1)
            for member in conf["conf"]['members']:
                newMember = Member(
                    member['_id'],
                    member['host'].split(':')[0],  # Get Host IP
                    member['priority']
                )
                state = newMember.CheckIfAlive()
                if state == True:
                    self.members.append(newMember)
            print('Members._getCurrentMembers: {}'.format(self.members))
        except Exception as error:
            print('Members._getCurrentMembers: WARN {}'.format(error))
