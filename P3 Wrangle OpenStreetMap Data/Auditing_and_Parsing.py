OSM_PATH = "south-bay_california.osm"

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE) #Compiler needed for street name auditing
LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

#List needed for audting street names - ignore street names that end with the following
expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Highway", "Wharf", "Boardwalk", "Strand", "Way", "I"]

#Dictionary needed for mapping incorrect street names to correct ones

mapping = { "St": "Street",
            "St.": "Street",
            "Ave.": "Avenue",
            "Ave": "Avenue",
            "blvd": "Boulevard",
            "Blvd": "Boulevard",
            "Blvd.": "Boulevard",
            "Arno": "Amo",
            "Hwy": "Highway"
          }

#Dictionary needed for the same task as above, but for the incomplete/unique mistakes that 
#require adding or removing information

unusual = {'A': 'Del Amo Boulevard', 
           '204': 'Pier Avenue',
           'Ness': 'Van Ness Avenue', 
           'B': 'Del Amo Boulevard', 
           '102': 'S Pacific Coast Highway', 
           'Hindry': 'Hindry Avenue'                  
          }

#Auditing Street Names Function
def update_name(name, mapping, unusual):
    m = street_type_re.search(name) #Searches for whatever is at the end of a given address, which is expected to be the street type
    street_type = m.group() #Allows us grab and work with the street type found
    if street_type not in expected: #If not one of the expected/acceptable street types, then move on towards cleaning
        if street_type not in mapping: #If not one of the standard abbrevation errors, then refer to 'unusual' dictionary for the replacement address
            name = unusual[street_type]
        else:
            corrected_street_type = mapping[street_type] #Refer to the 'mapping' dictionary for the correct street type
            name = name.replace(street_type, corrected_street_type) #Replace the abbreviated street type in the address with the correct street type
        
    return name


#Auditing Phone Numbers Function
def update_phone_num(phone_num):
    
    phone_num = re.sub("[-+() ]", "", phone_num) #Removes any instance of the included characters - "-", "+", "(", ")", and 
    #blank spaces
    
    if len(phone_num) > 10: #Some numbers end up being greater than 10 characters due to country codes. This ensures we 
        #grab just the area code + number when that happens.
        phone_num = phone_num[-10:]

    return phone_num[0:3] + "-" + phone_num[3:6] + "-" + phone_num[6:] #The decided format for the numbers

#Auditing Postal Codes Function
def update_postal_code(postalcode):
    loc = postalcode.find("90") #Outputs the index location of '90. Every zip begins with '90'.
    #This allows us to locate the zip code in cases where there is other information included we wouldn't need.
    postalcode = postalcode[loc:loc+5] #Returns strictly the zip code by returning '90' + the following 3 digits
    
    return postalcode


# Clean and shape node or way XML element to Python dict
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements

    if element.tag == 'node':
        for attribute in node_attr_fields:
            node_attribs[attribute] = element.attrib[attribute]
            
    if element.tag == 'way':
        for attribute in way_attr_fields:
            way_attribs[attribute] = element.attrib[attribute]
    
        counter = 0
        for tag in element.iter('nd'):
            dicnode = {}
            dicnode['id'] = element.attrib['id']
            dicnode['node_id'] = tag.attrib['ref']
            dicnode['position'] = counter
            counter += 1
            way_nodes.append(dicnode)
            
    for tag in element.iter('tag'):
        
        dictag = {}
        dictag['id'] = element.attrib['id']
        
        if ":" in tag.attrib['k']:
            keysplit = re.split(":",tag.attrib["k"],1)
            dictag['key'] = keysplit[1]
            
            if dictag['key'] == 'street':
                dictag['value'] = update_name(tag.attrib['v'], mapping, unusual)
                
            elif dictag['key'] == 'phone':
                dictag['value'] = update_phone_num(tag.attrib['v'])
                
            elif dictag['key'] == 'postcode':
                dictag['value'] = update_postal_code(tag.attrib['v'])
                
            else:
                dictag['value'] = tag.attrib['v']
                
            dictag['type'] = keysplit[0]
            
        else:
            dictag['key'] = tag.attrib['k']
            
            if dictag['key'] == 'street':
                dictag['value'] = update_name(tag.attrib['v', mapping, unusual])
                
            elif dictag['key'] == 'phone':
                dictag['value'] = update_phone_num(tag.attrib['v'])
                
            elif dictag['key'] == 'postcode':
                dictag['value'] == update_postal_code(tag.attrib['v'])
                
            else:
                dictag['value'] = tag.attrib['v']
                
            dictag['type'] = default_tag_type
            
        tags.append(dictag)
        
            
            
            
    if element.tag == 'node':
        return {'node': node_attribs, 'node_tags': tags}
    
    elif element.tag == 'way':
        return {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}


# ================================================== #
#               Helper Functions                     #
# ================================================== #
def get_element(osm_file, tags=('node', 'way', 'relation')):
    """Yield element if it is the right type of tag"""

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()


def validate_element(element, validator, schema=SCHEMA):
    """Raise ValidationError if element does not match schema"""
    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.iteritems())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))


class UnicodeDictWriter(csv.DictWriter, object):
    """Extend csv.DictWriter to handle Unicode input"""

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: (v.encode('utf-8') if isinstance(v, unicode) else v) for k, v in row.iteritems()
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


# ================================================== #
#               Main Function                        #
# ================================================== #
def process_map(file_in, validate):
    """Iteratively process each XML element and write to csv(s)"""

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])


process_map(OSM_PATH, validate=False)