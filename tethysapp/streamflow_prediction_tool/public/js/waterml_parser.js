/*****************************************************************************
 * FILE:    waterml_parser.js
 * AUTHOR:  Alan Snow
 * COPYRIGHT: © 2015 Alan D Snow. All rights reserved.
 * LICENSE: BSD 2-Clause
 * Code originally from https://github.com/crwr/wmlviewer
 * And modified for use in this app
 *****************************************************************************/

/*****************************************************************************
 *                      LIBRARY WRAPPER
 *****************************************************************************/

var WATERML = (function() {
    "use strict";
    /************************************************************************
    *                      MODULE LEVEL / GLOBAL VARIABLE DECLARATIONS
    *************************************************************************/
    var m_public_interface, m_property_list, m_units_list, 
        m_include_namespace, m_waterml_version, m_sig_figs;

    /************************************************************************
    *                      MODULE LEVEL / GLOBAL VARIABLE DEFINITIONS
    *************************************************************************/
    m_property_list = {
        properties: [
            {
                    name: "Discharge",
                    dimensions: "L^3/T",
                    displayUnits: "cfs",
                    seriesType: "area",
                    synonyms: ["Discharge", "Q", "Streamflow, ft&#179;/s", "Flow"],
            },
            {
                    name: "Runoff",
                    dimensions: "L",
                    displayUnits: "in", 
                    seriesType: "column",
                    synonyms: ["Runoff"],
            },        
            {
                    name: "Precipitation",
                    dimensions: "L",
                    displayUnits: "in",
                    seriesType: "column",                        
                    synonyms: [
                    "Precipitation", 
                    "IntervalPrecip", 
                    "Rainfall Total (1 day)", 
                    "Precipitation hourly total"
                ]
            },
            {
                    name: "Evaporation",
                    dimensions: "L",
                    displayUnits: "in",
                    seriesType: "area", 
                    synonyms: ["Evaporation", "Evapotranspiration", "total evapotranspiration"]
            },                        
            {
                    name: "Water Level",
                    dimensions: "L",
                    displayUnits: "ft",
                    seriesType: "area",                        
                    synonyms: ["Water Level", "S"],
            },        {
                    name: "Soil Moisture",
                    dimensions: "M/L^2",
                    displayUnits: "kg/m^2",
                    seriesType: "area",                        
                    synonyms: ["Soil Moisture", "0-100 cm layer 1 Soil moisture content", "0-100 cm  Average layer 1 soil moisture"],
            },
            {
                    name: "Storage",
                    dimensions: "L^3",
                    displayUnits: "acre-ft",
                    seriesType: "area",                        
                    synonyms: ["Storage", "Reservoir Storage", "ResV"],
            }
        ]
    };
    
    m_units_list = {
        dimensions: [
            {
                    name: "L^3/T",
                    commonUnit: "m^3/s",
                    units: [
                            {
                                name: "m^3/s",
                                synonyms: ["m^3/s", "cumec", "m&#179;/s", "m3/s", "m³/s", "cms"],
                                toCommon: 1,
                            },                        
                            {
                                name: "cfs",
                                synonyms: ["cfs", "ft&#179;/s", "ft3/s", "ft^3/s", "ft³/s"],
                                toCommon: 0.0283168466,
                            },
                            {
                                name: "l/s",
                                synonyms: ["l/s"],
                                toCommon: 0.001,
                            },                                
                    ]
            },
            {
                name: "L",
                commonUnit: "m",
                units: [
                        {
                            name: "m",
                            synonyms: ["m","meter", "metre"],
                            toCommon: 1,
                        },        
                        {
                            name: "cm",
                            synonyms: ["cm","centimeter", "centimetre"],
                            toCommon: 0.01,
                        },                
                        {
                            name: "ft",
                            synonyms: ["ft","foot", "feet"],
                            toCommon: 0.3048
                        },        
                        {
                            name: "in",
                            synonyms: ["in", "inch"],
                            toCommon: 0.0254,
                        },
                        {
                            name: "mm",
                            synonyms: ["mm", "millimeter", "millimetre"],
                            toCommon: 0.001,
                        },
                        {
                            name: "kg water/m^2",
                            synonyms: ["kg water/m^2", "kg/m^2", "Kilograms per square meter"],
                            toCommon: 0.001
                        }
                ]
            },
            {
                name: "M/L^2",
                commonUnit: "kg/m^2",
                units: [
                        {
                            name: "kg/m^2",
                            synonyms: ["kg/m^2", "Kilograms per square meter"],
                            toCommon: 1,
                        },
                ]
            },
            {
                name: "L^3",
                commonUnit: "m^3",
                units: [
                        {
                            name: "m^3",
                            synonyms: ["m^3", "cubic meter", "cubic meters"],
                            toCommon: 1,
                        },
                        {
                            name: "acre-ft",
                            synonyms: ["acre-ft", "acre-feet", "acre-foot", "ac-ft"],
                            toCommon: 1233.48185532
                        }
                ]
            }
        ]
    };

    /************************************************************************
    *                    PRIVATE FUNCTION DECLARATIONS
    *************************************************************************/
    var log10, roundToSignificantFigures, parseISO8601Date, convertUnits,
        convertPointUnits, getWMLVersion, getUnits, getObservations,  
        getSiteName, getObservedProperty, getPropertyDefaults, getValues,
        getActiveAHPSSeriesName;

    /************************************************************************
    *                    PRIVATE FUNCTION IMPLEMENTATIONS
    *************************************************************************/
    log10 = function(x) {
      return Math.log(x) / Math.LN10;
    };
    
    roundToSignificantFigures = function(num, n) {
        var d, power, magnitude, shifted;
        
        if(num == 0) {
            return 0;
        }
        d = Math.ceil(log10(num < 0 ? -num: num));
        power = n - Math.round(d);
        magnitude = Math.pow(10, power);
        shifted = Math.round(num*magnitude);
        return shifted/magnitude;
    };
    
    parseISO8601Date = function(s){
     //Source: http://n8v.enteuxis.org/2010/12/parsing-iso-8601-dates-in-javascript/
     //Modified to recognize additional formats
     
      // parenthese matches:
      // year month day    hours minutes seconds  
      // dotmilliseconds 
      // tzstring plusminus hours minutes
      var re = /(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(\.\d+)?(Z|([+-])(\d\d):(\d\d))/;
      var re2 = /(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)(\.\d+)/;
      var re3 = /(\d{4})-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)/;
      var re4 = /(\d{4})-(\d\d)-(\d\d)/;
      var d = [];
      d = s.match(re);
     
      // "2010-12-07T11:00:00.000-09:00" parses to:
      //  ["2010-12-07T11:00:00.000-09:00", "2010", "12", "07", "11",
      //     "00", "00", ".000", "-09:00", "-", "09", "00"]
      // "2010-12-07T11:00:00.000Z" parses to:
      //  ["2010-12-07T11:00:00.000Z", "2010", "12", "07", "11", 
      //     "00", "00", ".000", "Z", undefined, undefined, undefined]
      // "2010-12-07T11:00:00" parses to:
      //  ["2010-12-07T11:00:00.000Z", "2010", "12", "07", "11", 
      //     "00", "00", undefined, undefined, undefined, undefined, undefined]
      // "2010-12-07" parses to:
      // ["2010-12-07", "2010", "12", "07", "undefined", 
      //     "undefined", "undefined", undefined, undefined, undefined, undefined, undefined]
     
      if (! d) {
        d = s.match(re2);  
        if (! d) {  
            d = s.match(re3)
            if (! d) {
                d = s.match(re4)
                if (! d) {
                    throw "Couldn't parse ISO 8601 date string '" + s + "'";
                }
                d[4] = 0;
                d[5] = 0;
                d[6] = 0;
            }
        }
      }
     
      // parse strings, leading zeros into proper ints
      var a = [1,2,3,4,5,6,10,11];
      for (var i in a) {
        d[a[i]] = parseInt(d[a[i]], 10);
      }
      d[7] = parseFloat(d[7]);
     
     
      // Date.UTC(year, month[, date[, hrs[, min[, sec[, ms]]]]])
      // note that month is 0-11, not 1-12
      // see https://developer.mozilla.org/en/JavaScript/Reference/Global_Objects/Date/UTC
      var ms = Date.UTC(d[1], d[2] - 1, d[3], d[4], d[5], d[6]);
      // if there are milliseconds, add them
      if (d[7] > 0) {  
        ms += Math.round(d[7] * 1000);
      }
     
      // if there's a timezone, calculate it
      if (d[8] != "Z" && d[10]) {
        var offset = d[10] * 60 * 60 * 1000;
        if (d[11]) {
          offset += d[11] * 60 * 1000;
        }
        if (d[9] == "-") {
          ms -= offset;
        }
        else {
          ms += offset;
        }
      }
    
      return ms
      //return new Date(ms);
    };
    
    convertUnits = function(dimensions, unitFrom, unitTo){
        //Returns a conversion factor between two units, searching all synonyms in the attached wml-property-library.js
        //dimensions represents the standard dimensional abbreviation (L for length, M for mass, etc.)
        var fromConversion = -1;
        var toConversion = -1;
        
        for(var i=0;i<m_units_list.dimensions.length;i++){
            if (m_units_list.dimensions[i].name.toLowerCase() == dimensions.toLowerCase()){
                for (var j=0;j<m_units_list.dimensions[i].units.length;j++){
                    for (var k=0;k<m_units_list.dimensions[i].units[j].synonyms.length;k++){
                        if (m_units_list.dimensions[i].units[j].synonyms[k].toLowerCase() == unitFrom.toLowerCase()){
                            fromConversion = m_units_list.dimensions[i].units[j].toCommon;
                        }
                        if (m_units_list.dimensions[i].units[j].synonyms[k].toLowerCase() == unitTo.toLowerCase()){
                            toConversion = m_units_list.dimensions[i].units[j].toCommon;
                        }                                        
                    }
                }
            }
        }
        if ((fromConversion >0) && (toConversion>0)){
            return (fromConversion / toConversion);
        } else {
            return -1;
        }
    };

    convertPointUnits = function(series, dimensions, fromUnit, toUnit){
        //dimensions represents the standard dimensional abbreviation (L for length, M for mass, etc.)
        //fromUnit and toUnit can be any synonym listed in the relevant dimensions in wml-property-library.js 
        var result;
        var conversionFactor = convertUnits(dimensions, fromUnit, toUnit);
        result = series;
        if (conversionFactor>0){
            for (var i=0; i<result.length;i++){
                result[i][1] = isNaN(result[i][1]) ? null : roundToSignificantFigures(result[i][1] * conversionFactor, m_sig_figs);
            }
        }
        return result;
    }; 
  
    getWMLVersion = function(xml){
        var version;
        if (xml.find('om\\:OM_Observation').length>0) {
            version = 2;
            m_include_namespace = true;
        } else if (xml.find('OM_Observation').length>0) {
            version = 2;
            m_include_namespace = false;                
        } else if (xml.find('ns1\\:timeSeriesResponse').length>0){
            version = 1;
            m_include_namespace = true;                
        } else if (xml.find('timeSeriesResponse').length>0){
            version = 1;
            m_include_namespace = false;                        
        } else {
            version = 0;
        }
        m_waterml_version = version;
    };
    
    //***PARSE XML***
    getObservations = function(xml) {
        var query;
        if(m_waterml_version == 1){
            query = m_include_namespace ? "ns1\\:timeSeries" : "timeSeries";
        } else {
            query = m_include_namespace ? "om\\:OM_Observation" : "OM_Observation";
        }
        return xml.find(query);        
    };
    
    getSiteName = function(observation){
        var query;
        var result = null;
        if(m_waterml_version == 1){
            query = m_include_namespace ? "ns1\\:siteName" : "siteName";
            result=$($(observation).find(query)[0]).text();
        } else {
            query = m_include_namespace ? "om\\:featureOfInterest" : "featureOfInterest";
            result=$($(observation).find(query)[0]).attr("xlink:title");
        }        
        return result;
    };

    getActiveAHPSSeriesName = function(observation){
        var result = null;
        if(m_waterml_version == 2){
            var query1 = m_include_namespace ? "om\\:parameter" : "parameter";
            var query2 = m_include_namespace ? "om\\:name" : "name";
            result=$($(observation).find(query1).find(query2)[0]).attr("xlink:title");
        }        
        return result;
    };
    
    getObservedProperty = function(observation) {
        var query;
        var result = null;
        if(m_waterml_version == 1) {
            query = m_include_namespace ? "ns1\\:variableName" : "variableName";
            result=$($(observation).find(query)[0]).text();
        } else {
            query = m_include_namespace ? "om\\:observedProperty" : "observedProperty";
            result = $($(observation).find(query)[0]).attr("xlink:title");
        }
        return result;
    };
    
    getUnits = function(observation) {
        var query;
        var result = null;
        if(m_waterml_version == 1) {
            query = m_include_namespace ? "ns1\\:unitCode" : "unitCode";
            result=$($(observation).find(query)[0]).text();                                        
        } else {
            query = m_include_namespace ? "wml2\\:uom" : "uom"; 
            //<wml2:uom uom="CFS"/>               
            result = $($(observation).find(query)[0]).attr("code");
            //some WML services use attribute "uom" or "title" rather than "code". 
            if (result == undefined) {
                    result = $($(observation).find(query)[0]).attr("uom");
            }
            if (result == undefined) {
                    result = $($(observation).find(query)[0]).attr("xlink:title");
            }                
        }
        result = result ? result : ""; //prevents null exceptions
        return result;
    };
    
    getPropertyDefaults = function(property, sourceUnits, observation) {
        //Searches the attached wml-property-library.js for the 
        var query;
        var result = [];
        var propertyLabel = "";
        var dimensions = "";
        var displayUnits = "";
        var seriesType = "area";
        var conversionFactor;
        for(var j=0;j<m_property_list.properties.length;j++){
            for(var k=0;k<m_property_list.properties[j].synonyms.length;k++){
                if(m_property_list.properties[j].synonyms[k].toLowerCase() == property.toLowerCase()){
                    propertyLabel = m_property_list.properties[j].name;
                    dimensions = m_property_list.properties[j].dimensions;
                    displayUnits = m_property_list.properties[j].displayUnits;
                    seriesType = m_property_list.properties[j].seriesType;
                }
            }
        }
        if (propertyLabel == ""){
            //Unknown property
            propertyLabel = "Unknown Property";
        }                
        
        conversionFactor = convertUnits(dimensions, sourceUnits, displayUnits);
        
        //WML Version 1 services use unitCode, unitAbbreviation, and units differently. This checks whether the other approach should be tried.
        if (conversionFactor <0) {
            query = m_include_namespace ? "ns1\\:unitAbbreviation" : "unitAbbreviation";
            sourceUnits=$($(observation).find(query)[0]).text();
            conversionFactor = convertUnits(dimensions, sourceUnits, displayUnits);                                
        }        
        if (conversionFactor <0) {
            query = m_include_namespace ? "ns1\\:units" : "units";
            sourceUnits=$($(observation).find(query)[0]).text();
            conversionFactor = convertUnits(dimensions, sourceUnits, displayUnits);                                
        }                
        
        if (conversionFactor <0){
            //Unknown units
            dimensions = "";
            displayUnits = "Unknown Units";
            conversionFactor = 1;                        
        }
                
        result = {
            'propertyLabel': propertyLabel, 
            'dimensions': dimensions, 
            'sourceUnits': sourceUnits, 
            'displayUnits': displayUnits, 
            'conversionFactor': conversionFactor,
            'seriesType': seriesType,
        };
        return result;
    };
    
    getValues = function(observation) {
        //For WaterML 2, this currently only supports the Time-Value pair method of encoding
        var query, points, xText, yText, x, y, yRound;
        var result = [];
    
        if (m_waterml_version == 1){
            query = m_include_namespace ? "ns1\\:value" : "value";
            points = $(observation).find(query);                        
        }
        else {
            query = m_include_namespace ? "wml2\\:point" : "point";
            points = $(observation).find(query);
        }
    
        for(var j=0;j<points.length;j++)
        {
            if (m_waterml_version == 1){
                xText = $(points[j]).attr("dateTime");                            
                yText = $(points[j]).text();
            }
            else {
                query = m_include_namespace ? "wml2\\:time" : "time";				
                xText=$($(points[j]).find(query)[0]).text();
                query = m_include_namespace ? "wml2\\:value" : "value";				
                yText = $($(points[j]).find(query)[0]).text();
            }
            if (xText) {
                x = parseISO8601Date(xText);
                y = parseFloat(yText);
                yRound = isNaN(y) ? null : roundToSignificantFigures(y, m_sig_figs);
                result.push([x, yRound]);
            }
        }
        return result;
    };
    //***END PARSE XML***


    /************************************************************************
    *                        DEFINE PUBLIC INTERFACE
    *************************************************************************/
    /*
    * Library object that contains public facing functions of the package.
    * This is the object that is returned by the library wrapper function.
    * See below.
    * NOTE: The functions in the public interface have access to the private
    * functions of the library because of JavaScript function scope.
    */
    m_public_interface = {
        get_json_from_streamflow_waterml: function(waterml_doc, display_units, query_series_name) {
            // Initialize Global Variables
            m_include_namespace = null;
            m_waterml_version = null;

            //Convert to format useful for jQuery
            var xml = $(waterml_doc); 
            
            //Identify WML version and includeNamespace value 
            getWMLVersion(xml); //currently defined as global variables. may want to restrict the scope
            
            if (m_waterml_version < 1) {
                alert("Error adding series: WaterML Version not recognized");
                return null                
            } else {
                var all_series = [];
                //Extract data from xml and add to chart
                //WaterML2 allows for multiple time series observations per file, though typically there will be only one.
                var observations = getObservations(xml); 
                for (var i=0;i<observations.length;i++) {
                    //Get series metadata
                    var siteName = getSiteName(observations[i]);
                    var observedProperty = getObservedProperty(observations[i]);
                    var sourceUnits = getUnits(observations[i]);
                    var seriesValues = getValues(observations[i]);
                    if (seriesValues.length > 0){
                        //assume only dealing with flow
                        var displayUnits = "cms";
                        if(typeof display_units != undefined && display_units == "english") {
                            displayUnits = "cfs"
                        }
                        //for AHPS series, get the valid forecast
                        if (typeof query_series_name != 'undefined') {
                            var seriesName = getActiveAHPSSeriesName(observations[i]);
                            if (seriesName != 'undefined' && seriesName != null) {
                                if (seriesName.toLowerCase() == query_series_name.toLowerCase()) {
                                    //Convert series units
                                    all_series.push(convertPointUnits(seriesValues,"L^3/T", 
                                                    sourceUnits, displayUnits));
                                }
                            }
                        } else {
                            //Convert series units
                            all_series.push(convertPointUnits(seriesValues,"L^3/T", 
                                            sourceUnits, displayUnits));
                        }
                    }
                }
                if (all_series.length > 0) {
                    return all_series;
                } else {
                    return null;
                }
            }
        }
    };
        
    /************************************************************************
    *                  INITIALIZATION / CONSTRUCTOR
    *************************************************************************/
    $(function() {
        // Initialize Global Variables
        m_include_namespace = null;
        m_waterml_version = null;
        m_sig_figs = 4;
    });
    
    return m_public_interface;
}()); // End of package wrapper 