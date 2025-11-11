var ccm_xsd = `<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">

    <!--
    ========================================================
    REUSABLE BASE TYPES
    ========================================================
    A base type for structural elements (Node, District, Reference) that share
    the common attributes: id, name, quantity, and size.
    -->
    <xs:complexType name="MapElementBaseType">
        <xs:attribute name="id" type="xs:string" use="required"/>
        <xs:attribute name="name" type="xs:string" use="required"/>
        <xs:attribute name="quantity" type="xs:string" use="optional"/>
        <xs:attribute name="size" type="xs:string" use="optional"/>
        <xs:anyAttribute processContents="lax" namespace="##any"/>
    </xs:complexType>

    <!--
    ========================================================
    1 & 2. NODE and REFERENCE (Landmark) Elements
    ========================================================
    Both are defined using the common MapElementBaseType.
    -->
    <xs:element name="Node" type="MapElementBaseType"/>
    <xs:element name="Reference" type="MapElementBaseType"/>

    <!--
    ========================================================
    3. DISTRICT
    ========================================================
    A District is an extension of the base type and includes a sequence of
    ChildElement(s) which can be other Nodes, References, or Districts (recursive).
    -->
    <xs:complexType name="DistrictType">
        <xs:complexContent>
            <xs:extension base="MapElementBaseType">
                <xs:sequence>
                    <xs:choice minOccurs="0" maxOccurs="unbounded">
                        <xs:element ref="Node"/>
                        <xs:element ref="District"/>
                        <xs:element ref="Reference"/>
                    </xs:choice>
                </xs:sequence>
                <xs:attribute name="districtType" type="xs:string" use="required" />
                <xs:anyAttribute processContents="lax" namespace="##any"/>
            </xs:extension>
        </xs:complexContent>
    </xs:complexType>
    <xs:element name="District" type="DistrictType"/>


    <!--
    ========================================================
    4. RELATION (RDF-like)
    ========================================================
    Defines a relation with attributes for type, subject ID, and object ID,
    making it easily transformable into a Subject-Predicate-Object (SPO) triple.
    -->
    <xs:complexType name="RelationType">
        <xs:attribute name="id" type="xs:string" use="required"/>
        <xs:attribute name="relationType" type="xs:string" use="required"/>
        <xs:attribute name="subjectId" type="xs:string" use="required"/>
        <xs:attribute name="objectId" type="xs:string" use="required"/>
        <xs:anyAttribute processContents="lax" namespace="##any"/>
    </xs:complexType>
    <xs:element name="Relation" type="RelationType" />


    <!--
    ========================================================
    5. EDGE
    ========================================================
    Defines an Edge that separates two logical groups of elements.
    An edge can be passable (door, bridge, tunnel, etc.) or not (wall, river, mountain, etc.).
    -->
    <xs:complexType name="ElementGroupType">
        <xs:sequence>
            <!-- A group consists of one or more references to element IDs -->
            <xs:element name="ElementId" type="xs:string" maxOccurs="unbounded"/>
        </xs:sequence>
    </xs:complexType>

    <xs:complexType name="EdgeType">
        <xs:sequence>
            <xs:element name="GroupA" type="ElementGroupType"/>
            <xs:element name="GroupB" type="ElementGroupType"/>
        </xs:sequence>
        <xs:attribute name="id" type="xs:string" use="required"/>
        <xs:attribute name="name" type="xs:string" use="required"/>
        <xs:attribute name="edgeType" type="xs:string" use="required"/>
        <xs:attribute name="size" type="xs:string" use="optional"/>
    </xs:complexType>
    <xs:element name="Edge" type="EdgeType"/>


    <!--
    ========================================================
    6. PATH (Sequence of Activities)
    ========================================================
    A Path defines an ordered sequence of Steps, where each step specifies an element
    and an activity to be performed there.
    -->
    <xs:complexType name="PathStepType">
        <xs:attribute name="elementId" type="xs:string" use="required"/>
        <xs:attribute name="activity" type="xs:string" use="required"/>
    </xs:complexType>

    <xs:complexType name="PathType">
        <xs:sequence>
            <xs:element name="Step" type="PathStepType" maxOccurs="unbounded"/>
        </xs:sequence>
        <xs:attribute name="id" type="xs:string" use="required"/>
        <xs:attribute name="name" type="xs:string" use="required"/>
        <xs:attribute name="pathType" type="xs:string" use="required"/>
        <xs:anyAttribute processContents="lax" namespace="##any"/>
    </xs:complexType>
    <xs:element name="Path" type="PathType"/>


    <!--
    ========================================================
    ROOT ELEMENT: CognitiveMap
    ========================================================
    The main container for all the map's structural and relational elements.
    -->
    <xs:element name="CognitiveMap">
        <xs:complexType>
            <xs:sequence>
                <xs:choice minOccurs="0" maxOccurs="unbounded">
                    <xs:element ref="Node"/>
                    <xs:element ref="District"/>
                    <xs:element ref="Relation"/>
                    <xs:element ref="Reference"/>
                    <xs:element ref="Edge"/>
                    <xs:element ref="Path"/>
                </xs:choice>
            </xs:sequence>
        </xs:complexType>
    </xs:element>

</xs:schema>`;

var ccm_xml = `<?xml version="1.0" encoding="utf-8"?>
<CognitiveMap xsi:noNamespaceSchemaLocation="ccm.xsd"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    
    <District id="D001" name="Coffee Shop" districtType="open" size="huge">

        <District id="D100" name="Seating Area" districtType="open" size="huge" tip="Optional waiting area for customers. Some customers may sit here while waiting, while others prefer to stand at the pickup point.">
            <Node id="N101" name="Table"/>
            <Node id="N102" name="Chair"/>
        </District>

        <District id="D200" name="Service Area" districtType="open" size="large">
            <District id="D210" name="Counter" districtType="open" size="huge">
                <Node id="N212" name="Cash Register"/>
                <Node id="N211" name="Espresso Machine"/>
                <Node id="N201" name="Pastry Case"/>
                <Node id="N202" name="Mugs"/>
                <Node id="N213" name="Containers for Premade Coffee"/>
            </District>
            <District id="D211" name="Back Storage" districtType="open" size="medium">
                <Node id="N214" name="Coffee Machine"/>
            </District>
        </District>

        <District id="D300" name="Customer Waiting Area" districtType="open" size="medium" tip="Customers wait here after ordering until their drink is ready. Some stand here briefly while waiting, while others may sit in the Seating Area.">
            <Node id="N302" name="Pickup Point"/>
            <Node id="N301" name="Menu Board"/>
        </District>

    </District>

    <Node id="N001" name="Main Entrance Door"/>
    
    <Relation id="R07" relationType="separate" subjectId="N301" objectId="N302"/>
    <Relation id="R08" relationType="separate" subjectId="N302" objectId="N301"/>

    <Relation id="R01" relationType="near" subjectId="N101" objectId="N102"/>
    <Relation id="R02" relationType="near" subjectId="D200" objectId="D300"/>
    <Relation id="R03" relationType="near" subjectId="N001" objectId="D001"/>
    <Relation id="R04" relationType="near" subjectId="D100" objectId="D300"/>
    <Relation id="R05" relationType="near" subjectId="N211" objectId="N212"/>
    <Relation id="R06" relationType="functionalDependency" subjectId="N211" objectId="N212"/>

    <Edge id="E01" name="Counter" edgeType="passable">
        <GroupA>
            <ElementId>D200</ElementId>
        </GroupA>
        <GroupB>
            <ElementId>D100</ElementId>
        </GroupB>
    </Edge>

    <Edge id="E02" name="Counter Access" edgeType="passable">
        <GroupA>
            <ElementId>D210</ElementId>
        </GroupA>
        <GroupB>
            <ElementId>D300</ElementId>
        </GroupB>
    </Edge>

    <Path id="P01" name="Buy Coffee" pathType="activity" subject="Customer">
        <Step elementId="N001" activity="Enter"/>
        <Step elementId="N301" activity="Check Menu"/>
        <Step elementId="N212" activity="Order"/>
        <Step elementId="N302" activity="Wait and Collect Coffee"/>
    </Path>

    <Path id="P02" name="Make Coffee" pathType="activity" subject="Staff">
        <Step elementId="N213" activity="Retrieve Coffee Beans"/>
        <Step elementId="N202" activity="Clean Equipment"/>
        <Step elementId="N211" activity="Brew Espresso"/>
        <Step elementId="N214" activity="Refill Coffee Reservoir"/>
        <Step elementId="D210" activity="Serve Drinks"/>
    </Path>

</CognitiveMap>`;

const escapeXML = xml => xml.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');

document.getElementById("xsd-code").innerHTML = escapeXML(ccm_xsd);
document.getElementById("xml-code").innerHTML = escapeXML(ccm_xml);

document.querySelectorAll('.collapse-toggle').forEach(toggle => {
    toggle.addEventListener('click', (e) => {
        e.stopPropagation();
        const container = e.target.closest('.collapsible-code');
        container.classList.toggle('collapsed');
        e.target.textContent = container.classList.contains('collapsed') ? 'Show More (+)' : 'Show Less (-)';
    });
});

// Initialize syntax highlighting
hljs.highlightAll();


// Image Changing (Rotation)
function startImageRotation() {
    let currentIndex = 0;
    setInterval(() => {
        currentIndex = (currentIndex + 1) % 5;
        const ccmImg = document.getElementById('ccm-scene');
        const noccmImg = document.getElementById('noccm-scene');
        console.log(ccmImg, noccmImg)
        if (ccmImg) ccmImg.src = 'imgs/ccm' + (currentIndex+1) +'.jpg';
        if (noccmImg) noccmImg.src = 'imgs/noccm' + (currentIndex+1) +'.jpg';
    }, 10000); // every 10 seconds
}

// Start the rotation
startImageRotation();