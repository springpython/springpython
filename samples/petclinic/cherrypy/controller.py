"""
   Copyright 2006-2008 SpringSource (http://springsource.com), All Rights Reserved

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.       
"""
import cgi
import logging
import types
from datetime import date
from springpython.database.core import DaoSupport
from springpython.database.core import DatabaseTemplate
from springpython.database.core import RowMapper
from springpython.security import UsernameNotFoundException
from springpython.security.userdetails import UserDetailsService
from model import Owner
from model import Pet
from model import PetType
from model import Specialty
from model import Vet
from model import Visit
from springpython.security.vote import AccessDecisionVoter

class PetClinicController(DaoSupport):
    """This is a database-orienetd controller. Controllers are often responsible for providing data to populate views
    and also interface with other subsystems. For example, another version of the PetClinic controller could interface with a
    Directory Server to fetch data like telephone numbers and email addresses.
    
    All of the SQL operations use binding variables ("?") to prevent SQL injection attacks. This is a highly recommended
    feature in order to avoid security holes in your application."""
    
    def getVets(self):
        """Return a list of vets from the database."""
        return self.database_template.query("""
            SELECT
                id,
                first_name,
                last_name
            FROM vets
        """, rowhandler=VetRowMapper())
        
    def getOwners(self, lastName = ""):
        """Return a list of owners, filtered by partial lastname."""
        return self.database_template.query("""
            SELECT
                id,
                first_name,
                last_name,
                address,
                city,
                telephone
            FROM owners
            WHERE upper(last_name) like ?
            """, ("%"+lastName.upper()+"%",), OwnerRowMapper())
        
    def getOwner(self, id):
        """Return one owner."""
        return self.database_template.query("""
            SELECT
                id,
                first_name,
                last_name,
                address,
                city,
                telephone
            FROM owners
            WHERE id = ?
            """, (id,), OwnerRowMapper())[0]

    def addOwner(self, **kwargs):
        """Add an owner to the database."""
        rowsAffected = self.database_template.execute("""
            INSERT INTO owners
            (first_name, last_name, address, city, telephone)
            VALUES
            (?, ?, ?, ?, ?)
            """, (kwargs["firstName"], kwargs["lastName"], kwargs["address"], kwargs["city"], kwargs["telephone"]))
        return rowsAffected

    def updateOwner(self, id, address = "", city = "", telephone = ""):
        """Add an owner to the database."""
        rowsAffected = self.database_template.update("""
            UPDATE owners
            SET
                address   = ?,
                city      = ?,
                telephone = ?
            WHERE id = ?
            """, (address, city, telephone, id))
        return rowsAffected

    def getPets(self, owner):
        """Return pets belonging to a particular owner."""
        return self.database_template.query("""
            SELECT
                pets.id,
                pets.name,
                pets.birth_date,
                types.name
            FROM pets, owners, types
            WHERE owners.id = ?
            AND owners.id = pets.owner_id
            AND types.id = pets.type_id
            """, (owner.id,), PetRowMapper())

    def getPet(self, id):
        """Return pets belonging to a particular owner."""
        return self.database_template.query("""
            SELECT
                pets.id,
                pets.name,
                pets.birth_date,
                types.name
            FROM pets, types
            WHERE pets.id = ?
            AND types.id = pets.type_id
            """, (id,), PetRowMapper())[0]

    def getVisits(self, pet):
        """Return visits associated with a particular pet."""
        return self.database_template.query("""
            SELECT
                visits.visit_date,
                visits.description
            FROM pets, visits
            WHERE pets.id = ?
            AND pets.id = visits.pet_id
            """, (pet.id,), VisitRowMapper())

    def addPet(self, id, name, birthDate, type):
        """Store a new pet in the database."""
        rowsAffected = self.database_template.execute("""
                INSERT INTO pets
                (name, birth_date, type_id, owner_id)
                values
                (?, ?, ?, ?)
            """, (name, birthDate, type, id))
        return rowsAffected

    def getPetTypes(self):
        """Return visits associated with a particular pet."""
        return self.database_template.query("""
            SELECT types.id, types.name
            FROM types
            """, rowhandler=PetTypeRowMapper())

    def visitClinic(self, petId, description):
        """Record a visit to the clinic."""
        rowsAffected = self.database_template.execute("""
                INSERT INTO visits
                (pet_id, description, visit_date)
                values
                (?, ?, ?)
            """, (petId, description, date.today()))
        return rowsAffected

    def getVetSpecialties(self, vet):
        """Look up specialties associated with a particular veterinarian."""
        return self.database_template.query("""
                SELECT
                    specialties.id,
                    specialties.name
                FROM vets, vet_specialties, specialties
                WHERE vets.id = vet_specialties.vet_id
                AND vet_specialties.specialty_id = specialties.id
                AND vets.id = ?
            """, (vet.id,), SpecialtyRowMapper())

    def getUsername(self, id):
        """Look up the username associated with a user id"""
        return self.database_template.query_for_object("""
                SELECT username
                FROM owners
                WHERE id = ?
            """, (id,), types.StringType)
    
    def getUsers(self):
        """
        This function fetches the users out of the database, so someone trying out PetClinic
        can get the passwords to log in.
        """
        users = self.database_template.query_for_list("select username, password, ' ', enabled from users")
        for i in range(len(users)):
            authorities = [row for (row,) in self.database_template.query_for_list("select authority from authorities where username = ?", (users[i][0],))]
            users[i] = (users[i][0], users[i][1], authorities, users[i][3])
        return users
        
class VetRowMapper(RowMapper):
    """This is a row callback handler used in a database template call. It is used to process
    one row of data from a Vet-oriented query by mapping a Vet-record."""
    def map_row(self, row, metadata=None):
        vet = Vet()
        vet.id = row[0]
        vet.firstName = row[1]
        vet.lastName = row[2]
        return vet

class OwnerRowMapper(RowMapper):
    """This is a row callback handler used in a database template call. It is used to process
    one row of data from an owner-oriented query by mapping an Owner-record."""
    def map_row(self, row, metadata=None):
        owner = Owner()
        owner.id = row[0]
        owner.firstName = row[1]
        owner.lastName = row[2]
        owner.address = row[3]
        owner.city = row[4]
        owner.telephone = row[5]
        return owner

class PetRowMapper(RowMapper):
    """This is a row callback handler used in a database template call. It is used to process
    one row of data from a pet-oriented query by mapping an Pet-record."""
    def map_row(self, row, metadata=None):
        pet = Pet()
        pet.id = row[0]
        pet.name = row[1]
        pet.birthDate = row[2]
        pet.type = row[3]
        return pet

class PetTypeRowMapper(RowMapper):
    """This is a row callback handler used in a database template call. It is used to process
    one row of data from a visit-oriented query by mapping an Visit-record."""
    def map_row(self, row, metadata=None):
        petType = PetType()
        petType.id = row[0]
        petType.name = row[1]
        return petType

class SpecialtyRowMapper(RowMapper):
    """This is a row callback handler used in a database template call. It is used to process
    one row of data from a visit-oriented query by mapping an Visit-record."""
    def map_row(self, row, metadata=None):
        specialty = Specialty()
        specialty.id = row[0]
        specialty.name = row[1]
        return specialty

class VisitRowMapper(RowMapper):
    """This is a row callback handler used in a database template call. It is used to process
    one row of data from a visit-oriented query by mapping an Visit-record."""
    def map_row(self, row, metadata=None):
        visit = Visit()
        visit.date = row[0]
        visit.description = row[1]
        return visit

class OwnerVoter(AccessDecisionVoter):
    def __init__(self, controller=None):
        self.controller = controller
        self.logger = logging.getLogger("springpython.petclinic.controller")

    def supports(self, attr):
        """This voter will support a list.
        """
        if isinstance(attr, list) or (attr is not None and attr == "OWNER"):
            return True
        else:
            return False

    def vote(self, authentication, invocation, config):
        """Grant access if any of the granted authorities matches any of the required
        roles.
        """
        results = self.ACCESS_ABSTAIN
        for attribute in config:
            if self.supports(attribute):
                self.logger.debug("This OWNER voter will vote whether user owns this record.")
                results = self.ACCESS_DENIED
                id = cgi.parse_qs(invocation.environ["QUERY_STRING"])["id"][0]
                if self.controller.getUsername(id) == authentication.username:
                    self.logger.debug("User %s owns this record. Access GRANTED!" % authentication.username)
                    return self.ACCESS_GRANTED

        if results == self.ACCESS_ABSTAIN:
            self.logger.debug("This OWNER voter is abstaining from voting")
        elif results == self.ACCESS_DENIED:
            self.logger.debug("This OWNER voter did NOT own this record.")

        return results

    def __str__(self):
        return "<OWNER voter>"

class PreencodingUserDetailsService(UserDetailsService):
    """
    This user details service allows passwords to be created that are un-encoded, but
    will be encoded before the authentication step occurs. This is for demonstration
    purposes only, specifically to show the password encoders being plugged in.
    """
    def __init__(self, wrappedUserDetailsService = None, encoder = None):
        UserDetailsService.__init__(self)
        self.wrappedUserDetailsService = wrappedUserDetailsService
        self.encoder = encoder
        self.logger = logging.getLogger("springpython.petclinic.controller.PreencodingUserDetailsService")
        
    def load_user(self, username):
        user = self.wrappedUserDetailsService.load_user(username)
        user.password = self.encoder.encodePassword(user.password, None)
        self.logger.debug("Pre-converting %s's password to hashed format of %s, before authentication happens." % (username, user.password))
        return user
    
    def __str__(self):
        return "%s %s" % (self.encoder, self.wrappedUserDetailsService)
