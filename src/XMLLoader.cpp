//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.  
//
// Module   :  XMLLoader.cpp
// Author   :  Hyejung Hur
// Description: 
//
// Copyright (C) 2007 Hyejung Hur,  
// Electronic Visualization Laboratory, University of Illinois at Chicago
//
// This library is free software; you can redistribute it and/or modify it 
// under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation; either Version 2.1 of the License, or 
// (at your option) any later version.
//
// This library is distributed in the hope that it will be useful, but
// WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
// or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public 
// License for more details.
// 
// You should have received a copy of the GNU Lesser Public License along
// with this library; if not, write to the Free Software Foundation, Inc., 
// 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
//
// Direct questions, comments etc about Correlater Lib to hjhur@evl.uic.edu
//

#include <XMLLoader.h>
#include <iostream>
#include <string>

using namespace xercesc;
using namespace std;
//////////////////////////////////////////////////////////////////////
// Construction/Destruction
//////////////////////////////////////////////////////////////////////

CXMLLoader::CXMLLoader(Data* dataptr)
{
	_ulWarnings = 0;
	_ulErrors = 0;
	_dataptr = dataptr;
	_datatype = NOT_DEFINE_DATA;
	_found = false;
	_holeptr = NULL;
	_coreptr = NULL;
	_tieptr = NULL;
	_tieid = 0;
}

CXMLLoader::~CXMLLoader()
{
}

void CXMLLoader::endDocument()
{
	if ( _ulWarnings > 0 )
	{
	}

	if ( _ulErrors > 0 )
	{
	}
}

void CXMLLoader::endElement(const XMLCh* const name)
{
	CXMLElement *pParent = NULL;
	char *strElementName;

	CXMLElement *pElem = _stackEelementStack.top();
	_stackEelementStack.pop();
	if (!_stackEelementStack.empty())
	{
		pParent = _stackEelementStack.top();
	}

	strElementName = binToChar(name);

	switch(pElem->_nType)
	{
	case XML_CORRELATOR:
			break;
	case XML_DATA :
			break;
	case XML_HOLE :
			break;
	case XML_CORE :
			break;
	case XML_TIE :
			_tieptr = NULL;
			break;
	default:
		_ulWarnings++;
		break;
	}
	return;
}

void CXMLLoader::startDocument()
{
	_stackEelementStack.empty();

	_ulWarnings = 0;
	_ulErrors = 0;
}

void CXMLLoader::startElement(const XMLCh* const name, AttributeList& attributes)
{
	CXMLElement *pNewElement;
	char *strElementName;

	strElementName = binToChar( name );

	if ( stricmp(strElementName, "Correlator") == 0 )
	{
		pNewElement = new CXMLElement(strElementName, &attributes, XML_CORRELATOR);
		double valuef;
		if ( pNewElement->getValue( "version", valuef ) )	
		{
			// version 1.0
			//std::cout << "version : " << valuef << std::endl;
		}		
		_stackEelementStack.push(pNewElement);	
	}
	else if ( stricmp(strElementName, "Data") == 0 )
	{
		pNewElement = new CXMLElement(strElementName, &attributes, XML_DATA);
		char *value;	
		char* leg;
		char* site;
		double mudlineoffset, stretch;
		if ( pNewElement->getValue( "type", &value ) )
		{
			if ( strcmp(value, "affine table") == 0)
			{
				_datatype = AFFINE_TABLE;
			} else if ( strcmp(value, "splice table") == 0)
			{
				_datatype = SPLICE_TABLE;			
			} else if ( strcmp(value, "eld table") == 0)
			{
				_datatype = EQLOGDEPTH_TABLE;			
			}
			// CORE_DATA
		}
		if ( pNewElement->getValue( "leg", &leg ) )
		{
		}		
		if ( pNewElement->getValue( "site", &site ) )
		{
		}
		/*if ( pNewElement->getValuef( "mudlineoffset", mudlineoffset ) )
		{
		}
		if ( pNewElement->getValuef( "stretchrate", stretch ) )
		{
		}*/
						
		if ((strcmp(_dataptr->getSite(),site)==0) && (strcmp(_dataptr->getLeg(),leg)==0))
		{
			_found = true;
			//std::cout << "data : " << site << " " << leg << std::endl;
		}
		
		_stackEelementStack.push(pNewElement);	
			
	}
	else if ( stricmp(strElementName, "Hole") == 0 )
	{
		pNewElement = new CXMLElement(strElementName, &attributes, XML_HOLE);
		char *value;
		_holeptr = NULL;
		if ( pNewElement->getValue( "value", &value ) )
		{
			_holeptr = _dataptr->getHole(value[0]);
			//std::cout << "hole : " << value[0] << std::endl;
		}
		_stackEelementStack.push(pNewElement);	
	}
	else if ( stricmp(strElementName, "Core") == 0 )
	{	
		pNewElement = new CXMLElement(strElementName, &attributes, XML_CORE);
		_coreptr = NULL;
		if (_found == true)
		{	
			if (_datatype == AFFINE_TABLE)
			{
				loadAffineCoreData(pNewElement);	
			} else if (_datatype == SPLICE_TABLE)
			{
				loadSpliceCoreData(pNewElement);	
			}else if (_datatype == EQLOGDEPTH_TABLE)
			{
				loadAffineCoreData(pNewElement);
			}	
		}
		_stackEelementStack.push(pNewElement);		
	}
	else if ( stricmp(strElementName, "TIE") == 0 )
	{
		pNewElement = new CXMLElement(strElementName, &attributes, XML_TIE);
		if (_found == true && _datatype == SPLICE_TABLE)
		{	
			_tieptr = NULL;
			int tie_id;
			if ( pNewElement->getValuei( "id", tie_id ) )
			{
				_tieid = tie_id;
			}		
		}
		_stackEelementStack.push(pNewElement);	
	}
	else if ( stricmp(strElementName, "LogTie") == 0 )
	{
		pNewElement = new CXMLElement(strElementName, &attributes, XML_TIE);
		loadELDCoreData(pNewElement);	
	}	
	
}

void CXMLLoader::warning(const SAXParseException& exception)
{
	_ulWarnings++;
}

void CXMLLoader::loadAffineCoreData(CXMLElement *elem)
{
	double valuef;
	int	valuei;
	char *value_type;
	char *applied;
	
	if ( elem->getValuei( "id", valuei ) )
	{
	}

	if ( elem->getValue( "type", &value_type ) )
	{
	}
	
	if ( elem->getValue( "applied", &applied ) )
	{
	}
		
	if ( elem->getValue( "offset", valuef ) )
	{
	}	
		
	if (_holeptr != NULL)
	{
		_coreptr = _holeptr->getCoreByNo(valuei);
		double depth_offset = valuef;
		if (_coreptr != NULL) 
		{
			//std::cout << "core : " << valuei << ", " << depth_offset << std::endl;
			if (applied[0] == 'Y')
			{ 
				_coreptr->setDepthOffset(depth_offset, value_type[0], true, true);
			} else if (applied[0] == 'N')
			{
				_coreptr->setDepthOffset(depth_offset, value_type[0], false, true);
			}	
		}
	}

}

void CXMLLoader::loadSpliceCoreData(CXMLElement *elem)
{
	double valuef;
	int	valuei;
	char *value;


	int coreid;
	bool tied= false;
	char holeno;
	char coretype;
	char section[2];
	memset(section, 0, 2);
	data_range range;
	double mbsf, mcd;
	bool appendflag = false;
	bool allflag = false;
	
	if ( elem->getValuei( "id", valuei ) )
	{
		coreid = valuei;
	}
	if ( elem->getValue( "tietype", &value ) )
	{
		if (strcmp(value, "tied") == 0)
		{
			tied= true;
		} else if (strcmp(value, "append") == 0)
		{
			//std::cout << "append " << std::endl;
			appendflag = true;
			allflag = true;	
			tied= true;
		}
	}
	if ( elem->getValue( "hole", &value ) )
	{
		holeno = value[0];
	}
	if ( elem->getValue( "type", &value ) )
	{
		coretype = value[0];
	}	
	if ( elem->getValue( "section", &value ) )
	{
		//strcpy(section, value);
		section[0] = value[0];
		section[1] =  value[1];
	}
	if ( elem->getValue( "top", valuef ) )
	{
		range.top = valuef;
	}	
	if ( elem->getValue( "bottom", valuef ) )
	{
		range.bottom = valuef;
	}		

	if ( elem->getValue( "mbsf", valuef ) )
	{
		mbsf = valuef;
	}
	
	if ( elem->getValue( "mcd", valuef ) )
	{
		mcd = valuef;
	}		
	
	_holeptr = _dataptr->getHole(holeno);
	_coreptr = NULL;
	if (_holeptr != NULL)
	{
		_coreptr = _holeptr->getCoreByNo(coreid);
	}
	
	if (appendflag == true)
	{
		//std::cout << "range ..... " << range.top << " " << range.bottom << std::endl;
		if ((range.top >= 9999.0) && (range.bottom <= -9999.0))
		{
			allflag = false;
		}
	}

	if (_coreptr != NULL)
	{
		if (tied == false)
		{
			//std::cout <<  _coreptr->getName() << ":"  << _coreptr->getNumber() << " , " << section <<  "- tie-core : " << _tieid << " top : " << range.top << "," <<  range.bottom << " : " << "(" <<  mbsf << "," <<  mcd << ")" << coreid ;
			
			_tieptr = new Tie(_coreptr, coretype, section, range, mbsf, mcd, REAL_TIE, true);
			_tieptr->setOrder(_tieid);	
		} else 
		{
			if (_tieptr != NULL)
			{
				//std::cout << " ---" <<  _coreptr->getName() << ":"  << _coreptr->getNumber()  << " , " << section << " top : " << range.top << "," <<  range.bottom << " : "  << "(" <<  mbsf << "," <<  mcd << ")" << std::endl;
				if ((appendflag == true) && (allflag == false))
				{
					data_range range;
					Core* newcoreptr = _tieptr->getTied();
					_tieptr->setTied(_coreptr, 'x', "0", range);	
					_tieptr->setTieTo(newcoreptr, 'x', "0", range);	
					//std::cout << newcoreptr->getName() << newcoreptr->getNumber() << std::endl;
					_coreptr->addTie(_tieptr);
					//_tieptr->setTieTo(_coreptr, 'x', "0", range);	
					//_coreptr->addTie(_tieptr);
									
				} else 
				{
					_tieptr->setTieTo(_coreptr, coretype, section, range, mbsf, mcd);
					TieInfo* tiedInfo = _tieptr->getInfoTied();
					tiedInfo->m_coreptr->addTie(_tieptr);
					if (tiedInfo->m_mcd != mcd)
					{
						_tieptr->setConstrained(false);
					}				
				}
				_tieptr->setOrder(_tieid);	
				_tieptr->setAppend(appendflag, allflag);				
				
			}
		}
	} else 
	{
		std::cout << " NULL" << std::endl;
	}
	
}

void CXMLLoader::loadELDCoreData(CXMLElement* pElem)
{
	//_coreptr
}

void CXMLLoader::error(const SAXParseException& exception)
{
	_ulErrors++;
}

void CXMLLoader::fatalError(const SAXParseException& exception)
{
}

char *CXMLLoader::binToChar(const XMLCh * const string)
{
	char *buffer;
	int i = 0;

	if ( string==NULL )
		return NULL;

	while( string[i] != 0 )
	{
		i++;
	}

	buffer = new char[i+1];
	i = 0;
	while( string[i] != 0 )
	{
		buffer[i] = string[i];
		i++;
	}
	buffer[i] = 0;

	return buffer;
}

/* ***********************************************************************************
CXMLElement class
*********************************************************************************** */
CXMLElement::CXMLElement(char *name, AttributeList *attrib, XML_ELEMTYPE type, bool delobj)
{
	_strName = name;
	_attributeList = attrib;
	_nType = type;
	_pDeleteObj = delobj;
}

CXMLElement::~CXMLElement()
{
	if (_strName)
		delete []_strName;
	if (_pDeleteObj)
	{
		if (_pObject)
			delete []_pObject;
	}
}

bool CXMLElement::getValue( char *name, unsigned long &value )
{
	char *val = CXMLLoader::binToChar( _attributeList->getValue( name ) );
	if ( val != NULL )
	{
		value = atoi( val );
		delete []val;
	}
	else
		return false;
	return true;
}

bool CXMLElement::getValuei( char *name, int &value )
{
	char *val = CXMLLoader::binToChar( _attributeList->getValue( name ) );
	if ( val != NULL )
	{
		value = atoi( val );
		delete []val;
	}
	else
		return false;
	return true;
}

bool CXMLElement::getValue( char *name, double &value )
{
	char *val = CXMLLoader::binToChar( _attributeList->getValue( name ) );
	if ( val != NULL )
	{
		value = atof( val );
		delete []val;
	}
	else
		return false;
	return true;
}

bool CXMLElement::getValue( char *name, char ** value )
{
	char *val = CXMLLoader::binToChar( _attributeList->getValue( name ) );
	if ( val != NULL )
	{
		*value = val;
	}
	else
		return false;
	return true;
}
bool CXMLElement::getValueb( char *name, bool &value )
{
	char *val = CXMLLoader::binToChar( _attributeList->getValue( name ) );
	if ( val != NULL )
	{
		value = stricmp(val, "true") == 0 ? true : false;
	}
	else
		return false;
	return true;
}
