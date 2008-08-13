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
from sets import Set
from datetime import date

class Entity:
    def __init__(self, id = None):
        self.id = id
    def isNew(self):
        return self.id is None

class NamedEntity(Entity):
    def __init__(self, id = None, name = None):
        Entity.__init__(self, id)
        self.name = name

class Person(Entity):
    def __init__(self, id = None, firstName = None, lastName = None, address = None, city = None, telephone = None):
        Entity.__init__(self, id)
        self.firstName = firstName
        self.lastName = lastName
        self.address = address
        self.city = city
        self.telephone = telephone

class Owner(Person):
    def __init__(self, id = None, firstName = None, lastName = None, address = None, city = None, telephone = None, pets = Set()):
        Person.__init__(self, id, firstName, lastName, address, city, telephone)
        self.pets = pets
        
    def addPet(self, pet):
        self.pets.add(pet)
        pet.owner = self
        
    def getPet(self, name):
        for pet in self.pets:
            if pet.name == name:
                return pet
        return None

class Pet(NamedEntity):
    def __init__(self, id = None, name = None, birthDate = None, type = None, owner = None, visits = Set()):
        NamedEntity.__init__(self, id, name)
        self.birthDate = birthDate
        self.type = type
        self.owner = owner
        self.visits = visits
        
    def addVisit(self, visit):
        self.visits.add(visit)
        visit.pet = self

class PetType(NamedEntity):
    def __init__(self, id = None, name = None):
        NamedEntity.__init__(self, id, name)

class Specialty(NamedEntity):
    def __init__(self, id = None, name = None):
        NamedEntity.__init__(self, id, name)

class Vet(Person):
    def __init__(self, id = None, firstName = None, lastName = None, address = None, city = None, telephone = None, pets = Set(), specialties = Set()):
        Person.__init__(self, id, firstName, lastName, address, city, telephone)
        self.specialties = specialties
        
    def addSpecialty(self, specialty):
        self.specialties.add(specialty)

class Visit(Entity):
    def __init__(self, id = None, description = None, pet = None):
        Entity.__init__(self, id)
        self.date = date.today()
        self.description = description
        self.pet = pet
