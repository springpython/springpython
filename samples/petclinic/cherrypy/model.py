"""
    Copyright 2006-2007 Greg L. Turnquist, All Rights Reserved
    
    This file is part of PetClinic.

    PetClinic is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
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
