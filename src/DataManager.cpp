//////////////////////////////////////////////////////////////////////////////////
// CorrelatorLib - Correlator Class Library.   
//
// Module   :  DataManager.cpp
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

#include <iostream>

#ifdef DEBUG 
#include <time.h>
#endif

#ifdef WIN32
#include<stdio.h>
#include<time.h>      
#include<windows.h>
#endif

#include <DataManager.h>
#include <CoreTypes.h>
#include <DataParser.h>

#include <CullFilter.h>
#include <DecimateFilter.h>
#include <GaussianFilter.h>

using namespace std;

DataManager::DataManager( void )
: m_files(""), m_coreformat(MST95REPORT), m_column(0), m_stratType(DIATOMS)
{
	m_logdataptr = new Data();
	//m_logdataptr->setType(LOGTYPE);
#ifdef DEBUG
	time_t rawtime;
	struct tm* timeinfo;
	
	time(&rawtime);
	timeinfo = localtime(&rawtime);
	cout << "[DataManager] start of session : " << asctime(timeinfo) << endl;
#endif
}

DataManager::~DataManager( void )
{
	m_paths.clear();
	
	DataInfo* info = NULL;
	vector<DataInfo*>::iterator iter;
	for(iter = m_dataList.begin(); iter != m_dataList.end(); iter++)
	{
		info = (DataInfo*) *iter;
		if(info != NULL)
		{
			delete info;
			info = NULL;
		}
	}
	m_dataList.clear();
		
#ifdef DEBUG
	time_t rawtime;
	struct tm* timeinfo;
	
	time(&rawtime);
	timeinfo = localtime(&rawtime);
	cout << "[DataManager] close of session : " << asctime(timeinfo) << endl;
#endif	
	if(m_logdataptr)
	{
		delete m_logdataptr;
		m_logdataptr = NULL;
	}
}

void DataManager::init( void )
{
	m_files="";
	m_column = 0;
	m_stratType = DIATOMS;
	
	DataInfo* info = NULL;
	vector<DataInfo*>::iterator iter;
	for(iter = m_dataList.begin(); iter != m_dataList.end(); iter++)
	{
			info = (DataInfo*) *iter;
			if(info != NULL)
			{
					delete info;
					info = NULL;
			}
	}
	m_dataList.clear();
	
	if(m_logdataptr != NULL)
	{
		delete m_logdataptr;
		m_logdataptr = NULL;
		m_logdataptr = new Data();
		//m_logdataptr->setType(LOGTYPE);
	}
#ifdef DEBUG
	cout << "[DataManager] initialized " << endl;
#endif
}
	
int DataManager::registerPath( char* paths )
{
	string newpath(paths);
	int lastindex = newpath.length() -1;
	if(newpath[lastindex] != '/')
	{
		newpath += "/";
	} 
	
	// check 
	vector<string>::iterator iter;
	string existpath;
	for(iter = m_paths.begin(); iter != m_paths.end(); iter++) 
	{
		existpath = (string) *iter;
		if(existpath == newpath) 
		{
			return 0;
		}
	}
	
	m_paths.push_back(newpath);
	return 1;
} 

void DataManager::printPaths( void )
{
	vector<string>::iterator iter;
	string existpath;
	cout << "Paths : " << endl;
	int i = 1;
	for(iter = m_paths.begin(); iter != m_paths.end(); iter++, i++) 
	{
		existpath = (string) *iter;
		cout << i << ". " << existpath << endl;
	}
}

string DataManager::verifyFileReadable( const char* filename )
{
	string fullpath("");	

	FILE *fptr= NULL;
	int flag = 0;
	vector<string>::iterator iter;
	for(iter = m_paths.begin(); iter != m_paths.end(); iter++) 
	{
		fullpath = (string) *iter;
		fullpath += filename;
		
		fptr= fopen(fullpath.c_str(),"r+");
		if(fptr != NULL) 
		{
			flag = 1;
			break;
		} 
	}
	
	if(flag == 1) 
	{
		return fullpath;
	}
	
	fullpath = "";
	return fullpath;
	
}

Data* DataManager::load( const char* filename, Data* dataptr, char* annotation )
{	
	if(m_files.size() > 0) {
		int index = m_files.find(filename);
		if ( index  != string::npos )
		{
#ifdef DEBUG		
			cout << "ERROR : " << filename << " is already read " << endl;		
#endif
			return dataptr;
		}
	} 
	
	// todo : consider...
	string fullpath(filename);	
	FILE *fptr= fopen(filename,"r+");
	if(fptr == NULL) 
	{
		fullpath = verifyFileReadable(filename);
		if(fullpath == "") 
		{
#ifdef DEBUG		
			cout << "ERROR : " << filename << " could not find the registered directories " << endl;		
#endif
			return NULL;
		}	
	
		fptr= fopen(fullpath.c_str(),"r+");
		if(fptr == NULL) 
		{
#ifdef DEBUG		
			cout << "ERROR : " << filename << " could not be opened " << endl;
#endif
			return NULL;
		}	
	}

	int iscreatedHere = 0;	
	DataInfo* info = NULL;
	if(dataptr == NULL) 
	{
		dataptr = new Data();
		iscreatedHere = 1;
		info = new DataInfo(); 
		info->m_dataptr = dataptr;
		m_dataList.push_back(info);
		//cout << " new data " << endl;
	} else 
	{
		DataInfo* tempInfo = NULL;
		vector<DataInfo*>::iterator iter;
		for(iter = m_dataList.begin(); iter != m_dataList.end(); iter++)
		{
			tempInfo = (DataInfo*) *iter;
			if(tempInfo->m_dataptr->getLeg() == dataptr->getLeg())
			{
				info = tempInfo;
				break;
			}
		}
	}
	// check whether file is affine table or not
	int format = FindFormat(filename, fptr);
	if(format < 0) format = m_coreformat;
	
	int	ret = 0;
	switch (format)
	{
	case INTERNAL_REPORT:
		//cout << "INTERNAL_REPORT " << endl;
		dataptr->setDataFormat(format); 	
		ret = ReadCoreFormat(fptr, dataptr, m_coretype, annotation);	
		break;
	case AFFINE_TABLE:
		ret = ReadAffineTable(fptr, dataptr);
        break;
	case SPLICE_TABLE:		
		ret = ReadSpliceTable(fptr, dataptr);	
		break;
	case EQLOGDEPTH_TABLE:
		if(info->m_appliedAffineFilename.length() > 0) 
		{
			ret = ReadEqLogDepthTable(fptr, dataptr, info->m_appliedAffineFilename.c_str());
        } else 
		{
			ret = ReadEqLogDepthTable(fptr, dataptr, NULL);
		}
		break;
	case LOG:
	case ANCILL_LOG:
		{
			//cout << "log ------- " << endl;
			m_logInfo = "";
			if(m_logdataptr != NULL)
			{
				delete m_logdataptr;
				m_logdataptr = NULL;
				m_logdataptr = new Data();
				//m_logdataptr->setType(LOGTYPE);
			}			
			ret = ReadLog(fptr, "DEPTH", m_logdataptr, m_column, m_logInfo);
			
			/*for(int ith =0; ith < m_logInfo.size(); ith++)
			{
				printf("%c\n",m_logInfo[ith]);
			}*/
			
			//cout << m_logInfo.size() << endl;
			//m_logdataptr->debugPrintOut();
			//std::cout << "LOG FORMAT ------------" << ret << " : " << m_column << std::endl;
		}
		break;
	case XML_FILE:
		ret = ReadXMLFile(filename, dataptr);	
		break;
	case SPLICE:
		ret = ReadSplice(fptr, dataptr);
		break;
	case STRAT_TABLE:
		ret = ReadStrat(fptr, dataptr, m_stratType);
		break;
	case SPLICER_AGE:
		ret = ReadStratTable(fptr, dataptr);
		break;			
	}

	fclose(fptr);
	
	if (ret <= 0) return NULL;

	if(ret > 0) 
	{
		switch (format)
		{
		case INTERNAL_REPORT:
		case MST95REPORT:
		case TKREPORT:
		case ODPOTHER:
		case ODPOTHER1:
		case ODPOTHER2:
		case ODPOTHER3:
		case ODPOTHER4:
		case ODPOTHER5:
		case JANUSCLEAN:
		case JANUSORIG:
			{
				m_files += filename;
				int valideflag = dataptr->validate();

#ifdef DEBUG
				if(valideflag == 1) 
				{
					cout << "[DataManager] successfully loaded : " << fullpath  << " : data are VALID" << endl;
				} else 
				{
					cout << "[DataManager] successfully loaded : " << fullpath  << " : BUT data are NOT VALID" << endl;
				} 
#endif
				info->m_coreDataFormat.push_back(format);
				info->m_coreDataType.push_back(m_coretype);
				info->m_coreDataFiles.push_back(string(fullpath));
				
				if(info->m_appliedAffineFilename != "")
				{
						dataptr->init(ALL_TIE);
						dataptr->update();
						fptr= fopen(info->m_appliedAffineFilename.c_str(),"r+");
						if(fptr != NULL) 
						{
							ReadAffineTable(fptr, dataptr);
						}
						dataptr->update();
						fclose(fptr);
				}
				
				
			}
			break;
		case AFFINE_TABLE:
				m_files += filename;		
				info->m_appliedAffineFilename = fullpath;
#ifdef DEBUG
			cout << "[DataManager] successfully affine table is loaded : " << fullpath << endl;
#endif
				break;
		case SPLICE_TABLE:	
				m_files += filename;			
				info->m_appliedSpliceFilename = fullpath;
#ifdef DEBUG
			cout << "[DataManager] successfully splice table is loaded : " << fullpath << endl;
#endif
				break;

		case EQLOGDEPTH_TABLE:
				m_files += filename;		
				info->m_appliedEldFilename = fullpath;
#ifdef DEBUG
			cout << "[DataManager] successfully eqlogdepth table is loaded : " << fullpath << endl;
#endif
				break;
	case LOG:
	case ANCILL_LOG:
			info->m_appliedLogFilename = fullpath;
#ifdef DEBUG
			cout << "[DataManager] successfully log data is loaded : " << fullpath << endl;
#endif					
				break;
		case STRAT_TABLE: 
		case SPLICER_AGE:		
			info->m_startDataFiles.push_back(string(fullpath));
			info->m_stratDataType.push_back(m_stratType);
#ifdef DEBUG
			cout << "[DataManager] successfully strat data is loaded : " << fullpath << endl;
#endif		
				break;
		default:
#ifdef DEBUG
			cout << "[DataManager] successfully loaded : " << fullpath << endl;
#endif
			break;
		}
	} else 
	{
		return NULL;
	}

	/*
	if(iscreatedHere == 1) 
	{
		delete dataptr;
		dataptr = NULL;
		return NULL;
	}
	*/

	
	return dataptr;
}

Data* DataManager::loadAltSplice( const char* filename, Data* dataptr, int type, char* annotation )
{
	string fullpath(filename);	
	FILE *fptr= fopen(filename,"r+");
	if(fptr == NULL) 
	{
		fullpath = verifyFileReadable(filename);
		if(fullpath == "") 
		{
#ifdef DEBUG		
			cout << "ERROR : " << filename << " could not find the registered directories " << endl;		
#endif
			return NULL;
		}	
	
		fptr= fopen(fullpath.c_str(),"r+");
		if(fptr == NULL) 
		{
#ifdef DEBUG		
			cout << "ERROR : " << filename << " could not be opened " << endl;
#endif
			return NULL;
		}	
	}
	int ret = ReadSpliceTable(fptr, dataptr, true, type, annotation);

	fclose(fptr);
	
	if (ret > 0)
	{
#ifdef DEBUG
			cout << "[DataManager] successfully splice table is loaded : " << fullpath << endl;
#endif
		return dataptr;
	} 
	return NULL;	
}

void DataManager::loadCullTable( const char* filename, int coretype, Data* dataptr, char* annotation )
{
	string fullpath(filename);	
	FILE *fptr= fopen(filename,"r+");
	if(fptr == NULL) 
	{
		fullpath = verifyFileReadable(filename);
		if(fullpath == "") 
		{
#ifdef DEBUG		
			cout << "ERROR : " << filename << " could not find the registered directories " << endl;		
#endif
			return;
		}	
	
		fptr= fopen(fullpath.c_str(),"r+");
		if(fptr == NULL) 
		{
#ifdef DEBUG		
			cout << "ERROR : " << filename << " could not be opened " << endl;
#endif
			return;
		}	
	}
	
	//if (annotation != NULL)
	//	cout << "type = " << coretype << " annotation = " << annotation << endl;
	
	int ret = ReadCullTable(fptr, coretype, dataptr, annotation);
	
	if (ret > 0)
	{
#ifdef DEBUG
			cout << "[DataManager] successfully cull table is loaded : " << fullpath << endl;
#endif
	} 
		
	fclose(fptr);
}
	
void DataManager::cleanCore(Data* dataptr, int datatype)
{
	dataptr->remove(datatype);

	DataInfo* info = NULL;
	DataInfo* tempInfo = NULL;
	vector<DataInfo*>::iterator iter;
	for(iter = m_dataList.begin(); iter != m_dataList.end(); iter++)
	{
		tempInfo = (DataInfo*) *iter;
		if(tempInfo->m_dataptr->getLeg() == dataptr->getLeg())
		{
			info = tempInfo;
			break;
		}
	}

	if(info != NULL)
	{
		std::vector<std::string>::iterator fileiter = info->m_coreDataFiles.begin();
		std::vector<int>::iterator formatiter = info->m_coreDataFormat.begin();
		std::vector<int>::iterator typeiter = info->m_coreDataType.begin();

		int size = info->m_coreDataType.size();
		for(int i=0; i < size; i++)
		{
			if(info->m_coreDataType[i] == datatype)
			{
				info->m_coreDataType.erase(typeiter);
				info->m_coreDataFiles.erase(fileiter);
				info->m_coreDataFormat.erase(formatiter);
				i= -1;
				fileiter = info->m_coreDataFiles.begin();
				formatiter = info->m_coreDataFormat.begin();
				typeiter = info->m_coreDataType.begin();
				size = info->m_coreDataType.size();
			}
			else {
				fileiter++;
				formatiter++;
				typeiter++;
			}
		}
	}


}

int	DataManager::save( char* filename, Data* dataptr )
{
	if(dataptr == NULL || filename == NULL) return -1;
	int ret = WriteCoreData(filename, dataptr);

#ifdef DEBUG
	cout << "[DataManager] successfully data is saved : " << filename << endl;
#endif	
	return ret;
}
	
int	DataManager::saveHole( char* filename, Hole* holeptr )
{
	if(holeptr == NULL || filename == NULL) return -1;
	int ret = WriteCoreHole(filename, holeptr);

#ifdef DEBUG
	cout << "[DataManager] successfully data is saved : " << filename << endl;
#endif	
	return ret;
}


int	DataManager::save( char* read_filename, char* write_filename, int depth_idx, int data_idx )
{
	return WriteLog(read_filename, write_filename, depth_idx, data_idx);
}
	
	
int	DataManager::saveTimeSeries( char* agefilename, char* filename, Data* dataptr )
{
	if(dataptr == NULL || filename == NULL) return -1;
	DataInfo* info = NULL;
	int size = m_dataList.size();
	if (size > 0)
	{
		info = m_dataList[size-1];
	}
	int flag = 0;
	if (info != NULL)
	{
		if (info->m_appliedAffineFilename != "")
			flag = 1;
		if (info->m_appliedEldFilename != "")
			flag = 2;
	}	

	int ret = WriteAgeCoreData(agefilename, filename, dataptr, flag);

#ifdef DEBUG
	cout << "[DataManager] successfully data is saved : " << filename << endl;
#endif	
	return ret;
}
	
int	DataManager::saveTimeSeriesHole( char* agefilename, char* filename, Hole* holeptr )
{
	if(holeptr == NULL || filename == NULL) return -1;
	DataInfo* info = NULL;
	int size = m_dataList.size();
	if (size > 0)
	{
		info = m_dataList[size-1];
	}
	int flag = 0;
	if (info != NULL)
	{
		if (info->m_appliedSpliceFilename != "")
			flag = 1;
		if (info->m_appliedEldFilename != "")
			flag = 2;
	}	
	
	int ret = WriteAgeCoreHole(agefilename, filename, holeptr, flag);

#ifdef DEBUG
	cout << "[DataManager] successfully data is saved : " << filename << endl;
#endif	
	return ret;
}
	
int	DataManager::save( char* filename, Data* dataptr, char* affinefile )
{
	if(dataptr == NULL || filename == NULL) return -1;
	string fullpath(filename);	
	FILE *fptr= fopen(filename,"w+");
	if(fptr == NULL) 
	{
		return -1;
	}

	int ret = WriteSpliceTable(fptr, dataptr, affinefile);
	fclose(fptr);
	return ret;

}

		
int	DataManager::save( char* filename, Data* dataptr, int format )
{
	if(dataptr == NULL || filename == NULL) return -1;
	string fullpath(filename);	
	FILE *fptr= fopen(filename,"w+");
	if(fptr == NULL) 
	{
		return -1;
	}

	int ret = 0;
	switch (format)
	{
	case MST95REPORT:
	case TKREPORT:
	case ODPOTHER:
	case ODPOTHER1:
	case ODPOTHER2:
	case ODPOTHER3:
	case ODPOTHER4:
	case ODPOTHER5:
	case JANUSCLEAN:
	case JANUSORIG:
		break;
	case AFFINE_TABLE:
		{
			int pos = fullpath.find(".xml");
			if(pos != string::npos) 
			{
				//ret = WriteAffineTableinXML(fptr, dataptr);
			} else 
			{
				ret = WriteAffineTable(fptr, dataptr);
			}
		}
        break;
	case SPLICE_TABLE:
		{
			int pos = fullpath.find(".xml");
			DataInfo* info = NULL;
			//cout << " m_dataList = " << m_dataList.size() << endl;
			if(m_dataList.size() > 0)
			{
				info = (DataInfo*) *m_dataList.begin();
			}
			if(info == NULL)
			{
				if(pos != string::npos) 
				{
					//ret = WriteSpliceTableinXML(fptr, dataptr, NULL);
				} else 
				{
					ret = WriteSpliceTable(fptr, dataptr, NULL);
				}
			} else 
			{
				if(pos != string::npos) 
				{
					//ret = WriteSpliceTableinXML(fptr, dataptr, info->m_appliedAffineFilename.c_str());
				} else 
				{
					ret = WriteSpliceTable(fptr, dataptr, info->m_appliedAffineFilename.c_str());
				}
			}			
			
		}
		break;
	case EQLOGDEPTH_TABLE:
		{
			int pos = fullpath.find(".xml");		
			DataInfo* info = NULL;
			//cout << " m_dataList = " << m_dataList.size() << endl;
			if(m_dataList.size() > 0)
			{
				info = (DataInfo*) *m_dataList.begin();
			}
			if(info == NULL)
			{
				if(pos != string::npos) 
				{
					//ret = WriteEqLogDepthTableXML(fptr, dataptr, NULL);
				} else 
				{
					ret = WriteEqLogDepthTable(fptr, dataptr, NULL);
				}
			} else 
			{
				if(pos != string::npos) 
				{
					//ret = WriteEqLogDepthTableXML(fptr, dataptr, info->m_appliedAffineFilename.c_str());
				} else 
				{
					ret = WriteEqLogDepthTable(fptr, dataptr, info->m_appliedAffineFilename.c_str());
				}
			}
		}
		break;
	case LOG:
	case ANCILL_LOG:
		ret = WriteLog(fptr, dataptr, "DEPTH");
		break;
	case SPLICER_AGE:
		ret = WriteStratTable(fptr, dataptr);
		break;
	}
	
	fclose(fptr);
	return ret;
}

int DataManager::changeFormat(const char* infilename, const char* outfilename)
{
	return ChangeFormat(infilename, outfilename);
}

	
int	DataManager::save( char* filename, Hole* dataptr, const char* leg, const char* site, bool age )
{
	if(dataptr == NULL || filename == NULL) return -1;
	string fullpath(filename);	
	FILE *fptr= fopen(filename,"w+");
	if(fptr == NULL) 
	{
		return -1;
	}

	int ret = 0;
	if (age == false)
	{
		ret = WriteSplice(fptr, dataptr, leg, site);	
	} else 
	{
		string temp_path(filename);	
		temp_path += ".tmp";
		FILE *temp_fptr= fopen(temp_path.c_str(),"r+");
		ret = WriteAgeSplice(fptr, temp_fptr, dataptr, leg, site);	
		fclose(temp_fptr);
	}
	
	fclose(fptr);
	return ret;
}


void DataManager::cleanSplice( void )
{
	DataInfo* tempInfo = NULL;
	vector<DataInfo*>::iterator iter;
	for(iter = m_dataList.begin(); iter != m_dataList.end(); iter++)
	{
		tempInfo = (DataInfo*) *iter;
		tempInfo->m_appliedSpliceFilename = "";
	}
}

void DataManager::cleanLog( void )
{
	DataInfo* tempInfo = NULL;
	vector<DataInfo*>::iterator iter;
	for(iter = m_dataList.begin(); iter != m_dataList.end(); iter++)
	{
		tempInfo = (DataInfo*) *iter;
		tempInfo->m_appliedLogFilename = "";
	}
	if(m_logdataptr)
	{
		delete m_logdataptr;
		m_logdataptr = NULL;
		m_logdataptr = new Data();
		//m_logdataptr->setType(LOGTYPE);
	}	
}

void DataManager::cleanStrat( void )
{
	DataInfo* tempInfo = NULL;
	vector<DataInfo*>::iterator iter;
	for(iter = m_dataList.begin(); iter != m_dataList.end(); iter++)
	{
		tempInfo = (DataInfo*) *iter;
		tempInfo->m_startDataFiles.clear();
		tempInfo->m_stratDataType.clear();
	}	
}

void DataManager::setStratType( int type )
{
	m_stratType = type;
}

int	DataManager::getStratType( void )
{
	return m_stratType;
}

// return path number, return -1 if no path matched
int	DataManager::valifyData( char* filename )
{
	return 1;
}

void DataManager::setCullFile( char* filename )
{
	if(m_dataList.size() > 0)
	{
		DataInfo* info = (DataInfo*) *m_dataList.begin();
		info->m_appliedCullFilename = filename;
	}
}
void DataManager::setSelectedColumn( int column )
{
	m_column = column;
}
	
string* DataManager::getLogInfo( void )
{
	return &m_logInfo;
}

void DataManager::setCoreFormat( int format )
{
	m_coreformat = format;
}

int	DataManager::getCoreFormat( void )
{
	return m_coreformat;
}

void DataManager::setCoreType( int format )
{
	m_coretype = format;
}

int	DataManager::getCoreType( void )
{
	return m_coretype;
}

Data* DataManager::getLogData( void )
{
	return m_logdataptr;
}